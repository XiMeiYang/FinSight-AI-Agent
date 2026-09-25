import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) throw new Error("usage: build_research_excel.mjs snapshot.json output.xlsx");
const snapshot = JSON.parse(await fs.readFile(inputPath, "utf8"));
const wb = Workbook.create();
const navy = "#17365D";
const blue = "#D9EAF7";
const light = "#F5F8FB";
const border = { preset: "all", style: "thin", color: "#D9E2F3" };
const common = { font: { name: "Arial", size: 10, color: "#1F2937" }, verticalAlignment: "center" };
function safeCell(value) {
  if (typeof value === "string" && /^[=+\-@]/.test(value)) return "'" + value;
  return value;
}
function safeMatrix(rows) { return rows.map(row => row.map(safeCell)); }

function addSheet(name, title, headers, rows) {
  const sh = wb.worksheets.add(name);
  sh.showGridLines = false;
  sh.getRange("A1").values = [[safeCell(title)]];
  sh.getRange("A1").format = { font: { name: "Arial", size: 14, bold: true, color: navy } };
  sh.getRange("A2").values = [[safeCell(`Snapshot ${snapshot.snapshot_id} | as_of ${snapshot.as_of} | mode ${snapshot.data_mode || "unknown"}`)]];
  sh.getRange("A2").format = { font: { name: "Arial", size: 9, italic: true, color: "#5B6573" } };
  const start = 4;
  if (headers.length) {
    sh.getRangeByIndexes(start - 1, 0, 1, headers.length).values = [headers.map(safeCell)];
    sh.getRangeByIndexes(start - 1, 0, 1, headers.length).format = { fill: navy, font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center" };
    if (rows.length) sh.getRangeByIndexes(start, 0, rows.length, headers.length).values = safeMatrix(rows);
    sh.getRangeByIndexes(start - 1, 0, Math.max(rows.length + 1, 1), headers.length).format.borders = border;
    sh.getRangeByIndexes(start - 1, 0, Math.max(rows.length + 1, 1), headers.length).format.wrapText = false;
    sh.getRangeByIndexes(start - 1, 0, Math.max(rows.length + 1, 1), headers.length).format = { ...common, borders: border };
    sh.getRangeByIndexes(start - 1, 0, 1, headers.length).format = { fill: navy, font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", borders: border };
    sh.freezePanes.freezeRows(start);
    sh.getUsedRange().format.autofitColumns();
  }
  return sh;
}

const sec = snapshot.security || {};
const dq = snapshot.data_quality || {};
const latest = snapshot.market_data?.latest_bar || {};
const summaryRows = [
  ["Symbol", sec.symbol ?? null, "Company", sec.company_name ?? null],
  ["CIK", sec.cik ?? null, "Exchange", sec.exchange ?? null],
  ["Currency", sec.currency ?? null, "Evidence status", snapshot.summary?.evidence_status ?? null],
  ["Latest market observation", snapshot.summary?.latest_market_observation ?? null, "Market source", snapshot.market_data?.source ?? null],
  ["Latest close", latest.close ?? null, "Latest volume", latest.volume ?? null],
  ["Available SEC facts", snapshot.summary?.available_fact_count ?? null, "Available filings", snapshot.summary?.available_filing_count ?? null],
  ["Data quality", snapshot.data_quality?.status ?? null, "Missing sources", (snapshot.data_quality?.missing_sources || []).join(", ") || null],
  ["Point-in-Time filtered", snapshot.data_quality?.point_in_time_filtered_count ?? null, "Total excluded", snapshot.data_quality?.total_excluded_count ?? null],
  ["Limitations", (snapshot.summary?.limitations || []).join("; ") || null, "Warnings", (snapshot.data_quality?.warnings || []).join("; ") || null],
];
const overview = addSheet("Overview", "FinSight Research Snapshot", ["Field", "Value", "Field", "Value"], summaryRows);
overview.getRange("A5:D13").format.fill = light;
overview.getRange("A5:A13").format.font = { name: "Arial", size: 10, bold: true, color: navy };
overview.getRange("C5:C13").format.font = { name: "Arial", size: 10, bold: true, color: navy };

const marketRows = (snapshot.market_data?.bars || []).map(r => [r.symbol ?? sec.symbol ?? null, r.as_of ?? r.date ?? r.timestamp ?? null, r.open ?? null, r.high ?? null, r.low ?? null, r.close ?? null, r.volume ?? null, r.adjusted_close ?? null, r.currency ?? snapshot.market_data?.currency ?? null, r.source ?? snapshot.market_data?.source ?? null, r.retrieved_at ?? snapshot.market_data?.retrieved_at ?? null, snapshot.market_data?.adjustment ?? null]);
addSheet("Market_Daily", "Saved market observations", ["Symbol", "As of", "Open", "High", "Low", "Close", "Volume", "Adjusted close", "Currency", "Source", "Retrieved at", "Adjustment"], marketRows);

const factRows = (snapshot.sec_facts || []).map(r => [r.taxonomy ?? null, r.tag ?? null, r.label ?? null, r.value ?? null, r.unit ?? null, r.currency ?? null, r.period_start ?? null, r.period_end ?? null, r.available_at ?? r.filed_at ?? null, r.form ?? null, r.frame ?? null, r.accession_number ?? null, r.source ?? null, r.source_url ?? null, r.retrieved_at ?? null]);
const filingRows = (snapshot.sec_filings || []).map(r => [r.form ?? null, r.filing_date ?? null, r.report_date ?? null, r.acceptance_datetime ?? null, r.accession_number ?? null, r.primary_document ?? null, r.published_at ?? null, r.source ?? null, r.source_url ?? r.filing_url ?? null, r.retrieved_at ?? null, r.cik ?? sec.cik ?? null]);
addSheet("SEC_Filings", "SEC filings available by cutoff", ["Form", "Filing date", "Report date", "Acceptance datetime", "Accession", "Primary document", "Published at", "Source", "Source URL", "Retrieved at", "CIK"], filingRows);
addSheet("SEC_Facts", "SEC Company Facts available by cutoff", ["Taxonomy", "Tag", "Label", "Value", "Unit", "Currency", "Period start", "Period end", "Available at", "Form", "Frame", "Accession", "Source", "Source URL", "Retrieved at"], factRows);

const sourceRows = (snapshot.sources || []).map(r => [r.source_id ?? null, r.source_type ?? null, r.provider ?? null, r.source_url ?? null, r.published_at ?? null, r.data_as_of ?? null, r.retrieved_at ?? null, r.raw_sha256 ?? null, r.normalized_sha256 ?? null, r.input_file ?? null]);
addSheet("Sources", "Source and version metadata", ["Source ID", "Type", "Provider", "Source URL", "Published at", "Data as of", "Retrieved at", "Raw SHA-256", "Normalized SHA-256", "Input file"], sourceRows);

const qualityRows = [["Status", dq.status ?? null], ["Missing fields", (dq.missing_fields || []).join(", ") || null], ["Missing sources", (dq.missing_sources || []).join(", ") || null], ["Warnings", (dq.warnings || []).join(", ") || null], ["Conflicts", (dq.conflicts || []).join(", ") || null], ["Point-in-Time filtered", dq.point_in_time_filtered_count ?? null], ["Total excluded", dq.total_excluded_count ?? null], ["Filter counts", JSON.stringify(dq.filter_counts || {})]];
addSheet("Data_Quality", "Data quality and filtering", ["Field", "Value"], qualityRows);

const rr = snapshot.run_record || {};
const runRows = [
  ["Snapshot ID", snapshot.snapshot_id ?? null], ["Schema version", snapshot.schema_version ?? null], ["Created at", snapshot.created_at ?? null], ["As of", snapshot.as_of ?? null], ["Data mode", snapshot.data_mode ?? null], ["Network executed", rr.network_executed ?? null], ["Model calls", rr.model_calls ?? null], ["Run ID", rr.run_id ?? null], ["Run status", rr.status ?? null], ["Data quality status", dq.status ?? null], ["Missing fields", (dq.missing_fields || []).join(", ") || null], ["Conflicts", (dq.conflicts || []).join(", ") || null], ["Filter counts", JSON.stringify(dq.filter_counts || {})], ["Selected files", (rr.selected_files || []).join("; ") || null],
];
addSheet("Run_Record", "Offline run and data-quality record", ["Field", "Value"], runRows);

for (const sh of wb.worksheets.items) {
  const used = sh.getUsedRange();
  if (used) used.format.rowHeight = 18;
}
wb.recalculate();
const inspect = await wb.inspect({ kind: "table", range: "Overview!A1:D13", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 6 });
if (!inspect || !inspect.ndjson) throw new Error("workbook inspection failed");
await fs.mkdir(new URL(`file://${outputPath}`).pathname.replace(/\/[^/]*$/, ""), { recursive: true }).catch(() => {});
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(outputPath);
const reopened = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
const sheetCheck = await reopened.inspect({ kind: "sheet", include: "id,name" });
const expected = ["Overview", "Market_Daily", "SEC_Filings", "SEC_Facts", "Sources", "Data_Quality", "Run_Record"];
const names = (sheetCheck.ndjson || "").split("\n").filter(Boolean).map(line => JSON.parse(line).name);
if (JSON.stringify(names) !== JSON.stringify(expected)) throw new Error(`reopen sheet verification failed: ${JSON.stringify(names)}`);
