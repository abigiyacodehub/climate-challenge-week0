from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
PDF_PATH = REPORTS_DIR / "COP32_CLIMATE_EVIDENCE_REPORT.pdf"
COUNTRIES = ["Ethiopia", "Kenya", "Sudan", "Tanzania", "Nigeria"]


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_")


def load_data() -> pd.DataFrame:
    frames = []
    for country in COUNTRIES:
        path = PROCESSED_DIR / f"{slugify(country)}_daily_cleaned.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing cleaned data for {country}: {path}")
        frame = pd.read_csv(path, parse_dates=["date"])
        if frame.empty:
            raise ValueError(f"Cleaned data for {country} is empty")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def slope_per_year(group: pd.DataFrame, value_col: str) -> float:
    x = group["year"].to_numpy(dtype=float)
    y = group[value_col].to_numpy(dtype=float)
    if len(np.unique(x)) < 2:
        return float("nan")
    return float(np.polyfit(x, y, 1)[0])


def build_metrics(climate: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    annual_temperature = climate.groupby(["country", "year"], as_index=False).agg(
        mean_temperature_c=("t2m", "mean")
    )
    annual_precipitation = climate.groupby(["country", "year"], as_index=False).agg(
        annual_precipitation_mm=("prectotcorr", "sum")
    )

    temperature_summary = climate.groupby("country").agg(
        mean_temperature_c=("t2m", "mean"),
        mean_daily_max_c=("t2m_max", "mean"),
        hottest_day_c=("t2m_max", "max"),
    )
    precipitation_summary = annual_precipitation.groupby("country").agg(
        mean_annual_precipitation_mm=("annual_precipitation_mm", "mean"),
        driest_year_mm=("annual_precipitation_mm", "min"),
        wettest_year_mm=("annual_precipitation_mm", "max"),
        precipitation_cv=("annual_precipitation_mm", lambda s: s.std() / s.mean()),
    )

    heat_thresholds = climate.groupby("country")["t2m_max"].quantile(0.95).rename("heat_threshold_c")
    climate = climate.merge(heat_thresholds, on="country", how="left")
    climate["extreme_heat_day"] = climate["t2m_max"] >= climate["heat_threshold_c"]
    climate["dry_day"] = climate["prectotcorr"] < 1.0

    monthly_precip = climate.groupby(["country", "year", "month"], as_index=False).agg(
        monthly_precipitation_mm=("prectotcorr", "sum")
    )
    drought_thresholds = monthly_precip.groupby("country")["monthly_precipitation_mm"].quantile(0.20).rename(
        "drought_month_threshold_mm"
    )
    monthly_precip = monthly_precip.merge(drought_thresholds, on="country", how="left")
    monthly_precip["drought_month"] = (
        monthly_precip["monthly_precipitation_mm"] <= monthly_precip["drought_month_threshold_mm"]
    )

    extreme_summary = climate.groupby("country").agg(
        heat_threshold_c=("heat_threshold_c", "first"),
        extreme_heat_day_rate=("extreme_heat_day", "mean"),
        dry_day_rate=("dry_day", "mean"),
    ).join(
        monthly_precip.groupby("country").agg(drought_month_rate=("drought_month", "mean"))
    )

    temperature_trends = annual_temperature.groupby("country").apply(
        lambda g: slope_per_year(g, "mean_temperature_c")
    ).rename("temperature_trend_c_per_year")

    ranking_inputs = temperature_summary.join(precipitation_summary).join(extreme_summary).join(temperature_trends)
    features = [
        "mean_temperature_c",
        "temperature_trend_c_per_year",
        "precipitation_cv",
        "dry_day_rate",
        "drought_month_rate",
    ]
    scaled = ranking_inputs[features].copy()
    for column in features:
        min_value = scaled[column].min()
        max_value = scaled[column].max()
        scaled[column] = 0.0 if np.isclose(max_value, min_value) else (scaled[column] - min_value) / (max_value - min_value)

    ranking_inputs["vulnerability_score"] = scaled.mean(axis=1)
    ranking = ranking_inputs.sort_values("vulnerability_score", ascending=False).reset_index()
    ranking.insert(0, "rank", range(1, len(ranking) + 1))
    return annual_temperature, annual_precipitation, ranking


def extract_notebook_images(notebook_path: Path) -> list[bytes]:
    with notebook_path.open("r", encoding="utf-8") as handle:
        notebook = json.load(handle)
    images = []
    for cell in notebook["cells"]:
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            image_data = data.get("image/png")
            if image_data:
                if isinstance(image_data, list):
                    image_data = "".join(image_data)
                images.append(base64.b64decode(image_data))
    return images


def paragraph_style(name: str, parent: ParagraphStyle, **kwargs) -> ParagraphStyle:
    return ParagraphStyle(name=name, parent=parent, **kwargs)


def bullet_list(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style), leftIndent=12) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
    )


def add_image(story: list, image_bytes: bytes, caption: str, caption_style: ParagraphStyle, max_width: float = 6.4 * inch) -> None:
    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size
    ratio = min(max_width / width, 3.7 * inch / height)
    buffer = io.BytesIO(image_bytes)
    story.append(RLImage(buffer, width=width * ratio, height=height * ratio))
    story.append(Paragraph(caption, caption_style))
    story.append(Spacer(1, 0.16 * inch))


def table_from_dataframe(df: pd.DataFrame, columns: list[str], headers: list[str]) -> Table:
    rows = [headers]
    for _, row in df[columns].iterrows():
        formatted = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                formatted.append(f"{value:.3f}" if abs(value) < 10 else f"{value:.1f}")
            else:
                formatted.append(str(value))
        rows.append(formatted)
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c7d0d4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8f8")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#66747a"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "EthioClimate Analytics | COP32 Climate Evidence Report")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_report() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    climate = load_data()
    _, _, ranking = build_metrics(climate)
    compare_images = extract_notebook_images(ROOT / "notebooks" / "compare_countries.ipynb")
    ethiopia_images = extract_notebook_images(ROOT / "notebooks" / "ethiopia_eda.ipynb")

    styles = getSampleStyleSheet()
    title = paragraph_style("MediumTitle", styles["Title"], fontSize=24, leading=30, alignment=TA_CENTER, textColor=colors.HexColor("#16343d"), spaceAfter=14)
    subtitle = paragraph_style("Subtitle", styles["Normal"], fontSize=11, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#55656b"), spaceAfter=18)
    h1 = paragraph_style("H1", styles["Heading1"], fontSize=16, leading=21, textColor=colors.HexColor("#1f4e5f"), spaceBefore=14, spaceAfter=8)
    h2 = paragraph_style("H2", styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#2e6675"), spaceBefore=10, spaceAfter=6)
    body = paragraph_style("Body", styles["BodyText"], fontSize=9.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=8)
    caption = paragraph_style("Caption", styles["BodyText"], fontSize=8, leading=11, alignment=TA_LEFT, textColor=colors.HexColor("#5f6f75"), spaceAfter=8)
    callout = paragraph_style("Callout", styles["BodyText"], fontSize=10, leading=15, textColor=colors.HexColor("#16343d"), backColor=colors.HexColor("#eef6f3"), borderPadding=8, spaceAfter=10)

    story = [
        Paragraph("From Climate Data to COP32 Negotiation Evidence", title),
        Paragraph(
            "A Medium-style analytical report prepared for EthioClimate Analytics and the Ethiopian Ministry of Planning and Development",
            subtitle,
        ),
        Paragraph(
            "EthioClimate Analytics was engaged by the Ethiopian Ministry of Planning and Development to help prepare Ethiopia for hosting COP32 in Addis Ababa in 2027. The purpose of this work is practical: position Ethiopia as a credible, data-informed host and amplify Africa's voice in global climate negotiations.",
            callout,
        ),
        Paragraph("Business Objective", h1),
        Paragraph(
            "The analysis uses NASA POWER satellite-derived daily climate data from January 2015 through March 2026 for Ethiopia, Kenya, Sudan, Tanzania, and Nigeria. These countries provide a focused East, Horn, and West African comparison for temperature stress, rainfall reliability, drought exposure, and adaptation priorities.",
            body,
        ),
        Paragraph(
            "For a mixed technical and non-technical audience, the business objective is not simply to describe weather. It is to translate climate signals into negotiation-grade evidence: evidence clear enough to support a government position paper, financing request, or regional resilience agenda.",
            body,
        ),
        Paragraph("The Three-Layer Evidence Test", h2),
        bullet_list(
            [
                "<b>What is changing?</b> Establish the climate signal: trends against a baseline, with enough transparency to discuss uncertainty.",
                "<b>What did it cause?</b> Link climate stress to impact statistics such as yields, displacement, GDP losses, or disease burden. This project prepares the climate layer, while future work should add impact datasets.",
                "<b>What does it demand?</b> Convert evidence into a policy or finance ask, such as adaptation finance, early warning systems, drought preparedness, or loss-and-damage mechanisms.",
            ],
            body,
        ),
        Paragraph("Data and Method in Plain Language", h1),
        Paragraph(
            "NASA POWER provides satellite-derived and modeled daily weather indicators. For this project, the notebooks collected daily mean temperature, daily maximum and minimum temperature, corrected precipitation, relative humidity, and wind speed. The local workflow keeps raw and cleaned CSV files out of Git while preserving code that can regenerate them.",
            body,
        ),
        Paragraph(
            "Data quality checks looked for missing values, duplicate dates, incomplete date coverage, empty files, unexpected API schemas, and NASA missing-value sentinels. The notebooks replace `-999` sentinels with missing values, remove duplicate dates, reindex observations to a daily calendar, and interpolate numeric weather gaps only after documenting that decision.",
            body,
        ),
    ]

    if ethiopia_images:
        add_image(
            story,
            ethiopia_images[0],
            "Figure 1. Ethiopia annual mean temperature trend from the EDA notebook. The figure is used to introduce the baseline trend question: what is changing over time?",
            caption,
        )

    story.extend(
        [
            Paragraph("Completed Analysis", h1),
            Paragraph("Task 2: Country EDA", h2),
            Paragraph(
                "The Ethiopia EDA notebook demonstrates the end-to-end method: load NASA POWER data, profile quality issues, clean the daily series, export a local cleaned dataset, and interpret visual patterns. The main observed pattern is strong rainfall seasonality, with rainfall concentrated in the rainy months and comparatively dry conditions outside that window.",
                body,
            ),
            Paragraph(
                "The same cleaning logic is then applied in the cross-country notebook for all five countries. This allows the report to compare countries using consistent definitions rather than mixing incompatible local assumptions.",
                body,
            ),
            Paragraph("Task 3: Cross-Country Comparison", h2),
            Paragraph(
                "The comparison notebook combines cleaned datasets for Ethiopia, Kenya, Sudan, Tanzania, and Nigeria. It compares annual mean temperature, annual precipitation totals, monthly rainfall patterns, extreme heat days, dry days, drought months, and a composite climate vulnerability score.",
                body,
            ),
        ]
    )

    if len(compare_images) >= 1:
        add_image(
            story,
            compare_images[0],
            "Figure 2. Annual mean temperature comparison across the five countries. This shows baseline temperature differences and year-to-year movement.",
            caption,
        )
    if len(compare_images) >= 2:
        add_image(
            story,
            compare_images[1],
            "Figure 3. Annual precipitation comparison. The figure highlights rainfall reliability and variability, central concerns for adaptation finance.",
            caption,
        )
    if len(compare_images) >= 3:
        add_image(
            story,
            compare_images[2],
            "Figure 4. Monthly precipitation distributions. The visual makes seasonality visible rather than leaving rainfall totals as abstract numbers.",
            caption,
        )
    if len(compare_images) >= 4:
        add_image(
            story,
            compare_images[3],
            "Figure 5. Extreme heat, dry-day, and drought-month indicators. These are the event-frequency signals most relevant to preparedness and resilience planning.",
            caption,
        )

    ranking_table = ranking[
        [
            "rank",
            "country",
            "vulnerability_score",
            "mean_temperature_c",
            "temperature_trend_c_per_year",
            "precipitation_cv",
            "dry_day_rate",
            "drought_month_rate",
        ]
    ].copy()

    story.extend(
        [
            Paragraph("Climate Vulnerability Ranking", h1),
            Paragraph(
                "The vulnerability ranking is a relative screening index, not a final national vulnerability assessment. It combines normalized indicators for heat exposure, warming trend, precipitation variability, dry-day frequency, and drought-month frequency. Higher scores indicate countries that should receive closer policy attention in this climate-only screening.",
                body,
            ),
            table_from_dataframe(
                ranking_table,
                [
                    "rank",
                    "country",
                    "vulnerability_score",
                    "mean_temperature_c",
                    "temperature_trend_c_per_year",
                    "precipitation_cv",
                    "dry_day_rate",
                    "drought_month_rate",
                ],
                ["Rank", "Country", "Score", "Mean T", "T trend", "Rain CV", "Dry days", "Drought months"],
            ),
            Spacer(1, 0.14 * inch),
        ]
    )
    if len(compare_images) >= 5:
        add_image(
            story,
            compare_images[4],
            "Figure 6. Composite climate vulnerability ranking. The ranking turns multiple climate indicators into a single prioritization view for discussion.",
            caption,
        )

    top = ranking.iloc[0]
    driest = ranking.sort_values("dry_day_rate", ascending=False).iloc[0]
    variable = ranking.sort_values("precipitation_cv", ascending=False).iloc[0]
    story.extend(
        [
            Paragraph("What the Evidence Means for COP32", h1),
            Paragraph(
                f"In this screening, {top['country']} ranks highest on the composite climate vulnerability score. {driest['country']} has the highest dry-day rate, while {variable['country']} shows the highest annual precipitation variability. These signals matter because negotiations are strongest when they connect observed climate stress to a concrete ask.",
                body,
            ),
            Paragraph("Strategic Recommendations", h2),
            bullet_list(
                [
                    "<b>Position Ethiopia as a data-informed host.</b> Use transparent satellite-derived evidence to show that COP32 in Addis Ababa is anchored in measurable African climate realities, not only political messaging.",
                    "<b>Frame adaptation finance around rainfall reliability.</b> Countries with high dry-day rates or rainfall variability need financing for water storage, drought contingency plans, and climate-smart agriculture.",
                    "<b>Invest in early warning systems.</b> Extreme heat and drought-month indicators support a regional case for stronger forecasting, local alert systems, and preparedness budgets.",
                    "<b>Prepare the loss-and-damage evidence chain.</b> The current climate indicators answer what is changing. To support stronger claims, Ethiopia and partners should next connect these hazards to crop losses, displacement, disease burden, and infrastructure damage.",
                    "<b>Use the five-country comparison to amplify Africa's voice.</b> The evidence shows that African climate risk is not one uniform story. COP32 messaging should preserve that diversity while arguing for a shared financing platform.",
                ],
                body,
            ),
            Paragraph("Limitations and Future Work", h1),
            Paragraph(
                "This analysis is intentionally honest about scope. NASA POWER is appropriate for consistent multi-country screening, but it is satellite-derived and modeled, not a replacement for all ground-station observations. The analysis uses capital or major administrative city points, so it does not represent every agro-ecological zone inside each country.",
                body,
            ),
            Paragraph(
                "The vulnerability ranking is climate-only. It does not yet include exposure, poverty, infrastructure quality, health-system capacity, irrigation access, conflict, or adaptive capacity. That means it is useful for screening and storytelling, but not sufficient by itself for final finance allocation.",
                body,
            ),
            Paragraph("Meaningful next steps include:", h2),
            bullet_list(
                [
                    "Add gridded or multi-city coverage inside each country to better represent national climate diversity.",
                    "Validate NASA POWER estimates against national meteorological station data where available.",
                    "Link climate indicators to impact datasets: crop yields, food prices, displacement, malaria or heat-health burden, and GDP loss estimates.",
                    "Quantify uncertainty using baseline comparisons, confidence intervals, and sensitivity tests for drought and heat thresholds.",
                    "Build the `dashboard-dev` branch into a stakeholder-facing tool for ministry briefings and COP32 preparation.",
                ],
                body,
            ),
            Paragraph("Closing Note", h1),
            Paragraph(
                "The main value of this project is movement from analysis to position. The notebooks create reproducible climate evidence; the comparison turns that evidence into regional insight; and this report translates the results into a policy language suitable for a government audience preparing for COP32.",
                body,
            ),
        ]
    )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="COP32 Climate Evidence Report",
        author="EthioClimate Analytics",
    )
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


if __name__ == "__main__":
    build_report()
    print(PDF_PATH)
