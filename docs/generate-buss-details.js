const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat,
} = require("docx");

// ── Color palette (matches TECH_DETAILS.docx) ──
const DARK_BLUE = "1B3A5C";
const MID_BLUE = "2E5A88";
const LIGHT_BLUE = "D5E8F0";
const ACCENT_BLUE = "2E75B6";
const GRAY = "666666";
const LIGHT_GRAY = "F2F2F2";
const TABLE_BORDER_COLOR = "CCCCCC";

// ── Reusable border config ──
const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: TABLE_BORDER_COLOR };
const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

// ── Page constants (US Letter, 1" margins) ──
const PAGE_WIDTH = 12240;
const PAGE_HEIGHT = 15840;
const MARGIN = 1440;
const CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN; // 9360

// ── Helper: header cell ──
function headerCell(text, width) {
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: DARK_BLUE, type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, font: "Arial", size: 20, color: "FFFFFF" })] })],
  });
}

// ── Helper: body cell ──
function bodyCell(text, width, opts = {}) {
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({
      children: [new TextRun({
        text,
        font: "Arial",
        size: 20,
        bold: opts.bold || false,
        color: opts.color || "333333",
      })],
    })],
  });
}

// ── Helper: simple paragraph ──
function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after || 200 },
    children: [new TextRun({
      text,
      font: "Arial",
      size: opts.size || 22,
      bold: opts.bold || false,
      italics: opts.italics || false,
      color: opts.color || "333333",
    })],
  });
}

// ── Helper: multi-run paragraph (for bold+normal in same line) ──
function multiPara(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after || 200 },
    children: runs.map(r => new TextRun({
      text: r.text,
      font: "Arial",
      size: r.size || 22,
      bold: r.bold || false,
      italics: r.italics || false,
      color: r.color || "333333",
    })),
  });
}

// ── Build the document ──
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: DARK_BLUE },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: MID_BLUE },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: MID_BLUE },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "numbered",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  sections: [
    // ════════ COVER PAGE ════════
    {
      properties: {
        page: {
          size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      children: [
        new Paragraph({ spacing: { before: 3000 } }),
        new Paragraph({
          spacing: { after: 200 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "FinDocIQ", font: "Arial", bold: true, color: DARK_BLUE, size: 72 })],
        }),
        new Paragraph({
          spacing: { after: 100 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Business Details Guide", font: "Arial", color: MID_BLUE, size: 40 })],
        }),
        new Paragraph({
          spacing: { after: 100 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Financial Document Intelligence Platform", font: "Arial", color: GRAY, size: 28 })],
        }),
        new Paragraph({
          spacing: { after: 100 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Strategic Alignment & Business Value", font: "Arial", color: GRAY, size: 28 })],
        }),
        new Paragraph({ spacing: { before: 800 } }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 0 },
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: ACCENT_BLUE, space: 1 } },
          children: [],
        }),
        new Paragraph({
          spacing: { before: 200 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Version 1.0  |  April 2026", font: "Arial", color: GRAY, size: 22 })],
        }),
      ],
    },

    // ════════ TABLE OF CONTENTS ════════
    {
      properties: {
        page: {
          size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT_BLUE, space: 1 } },
            children: [new TextRun({ text: "FinDocIQ  |  Business Details Guide", font: "Arial", size: 18, color: GRAY })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Page ", font: "Arial", size: 18, color: GRAY }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: GRAY })],
          })],
        }),
      },
      children: [
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Table of Contents")] }),
        para("1. Executive Summary"),
        para("2. The Problem: Unstructured Data in Financial BPOs"),
        para("3. The Solution: AI-Augmented Document Operations"),
        para("4. What the MVP Does Today"),
        para("5. Business Value Metrics"),
        para("6. The Engineering Force Multiplier"),
        para("7. Strategic Alignment with nuDesk"),
        para("8. Roadmap: From MVP to Enterprise"),
        para("9. Go-to-Market Positioning"),
      ],
    },

    // ════════ MAIN CONTENT ════════
    {
      properties: {
        page: {
          size: { width: PAGE_WIDTH, height: PAGE_HEIGHT },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT_BLUE, space: 1 } },
            children: [new TextRun({ text: "FinDocIQ  |  Business Details Guide", font: "Arial", size: 18, color: GRAY })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Page ", font: "Arial", size: 18, color: GRAY }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: GRAY })],
          })],
        }),
      },
      children: [
        // ── 1. Executive Summary ──
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. Executive Summary")] }),
        para("FinDocIQ is a working MVP that automates document-heavy workflows for financial services BPOs. Upload a PDF \u2014 bank statement, loan application, or pay stub \u2014 and the system extracts structured data via OCR and AI, computes risk metrics, flags anomalies, indexes the content for semantic search, and lets analysts query documents in natural language with sourced answers. Built in 48 hours, it converts 15\u201325 minutes of manual data entry per file into under 30 seconds of automated, verifiable processing."),
        para("The core strategic bet: FinDocIQ is not a standalone SaaS product. It is a prototype of an intelligent DeskMate \u2014 a specialized digital companion purpose-built for financial services workflows \u2014 designed as internal, proprietary infrastructure for AI-native BPOs like nuDesk."),

        // ── 2. The Problem ──
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. The Problem: Unstructured Data in Financial BPOs")] }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("The Unit Economics of Legacy Operations")] }),
        para("In a standard financial BPO or lending environment, a loan operations analyst processes roughly 20 to 30 files per day. Each file requires 15 to 25 minutes of manual data entry, cross-referencing, and verification. That equates to over 6 hours a day of repetitive, error-prone \u201Cstare-and-compare\u201D labor that generates zero strategic value."),
        para("This manual bottleneck drives real business pain:"),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Slow origination cycles. ", bold: true, font: "Arial", size: 22 }), new TextRun({ text: "The average mortgage process takes 30 to 60 days, driven primarily by manual document verification \u2014 not the complexity of the credit decision itself.", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Application abandonment. ", bold: true, font: "Arial", size: 22 }), new TextRun({ text: "Processing delays cause borrowers to defect to competitors with faster digital experiences, directly destroying revenue.", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 200 },
          children: [new TextRun({ text: "Costly errors. ", bold: true, font: "Arial", size: 22 }), new TextRun({ text: "Human fatigue introduces data entry mistakes that elevate compliance risks and require expensive downstream re-work by senior underwriting staff.", font: "Arial", size: 22 })],
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("The Nearshore Wage Pressure")] }),
        para("Leading AI-native BPOs utilize nearshore talent (e.g., in Mexico) to maintain time-zone alignment and cultural affinity with U.S. markets. However, technology wages in Mexico have surged 42% over a two-year period, tightening operational margins. The traditional strategy of linearly scaling human headcount to meet demand is no longer financially viable."),
        para("FinDocIQ acts as a direct hedge against this wage inflation by shifting the operational model from human-driven data entry to human-in-the-loop AI validation. Analysts elevate from data-entry clerks to strategic financial reviewers."),

        // ── 3. The Solution ──
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. The Solution: AI-Augmented Document Operations")] }),
        para("FinDocIQ replaces manual effort with four interconnected, automated capabilities:"),
        new Paragraph({
          numbering: { reference: "numbered", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Zero-egress document ingestion. ", bold: true, font: "Arial", size: 22 }), new TextRun({ text: "Analysts upload raw PDFs. Localized OCR (PaddleOCR running on-host, not a cloud API) digitizes the text. No sensitive financial data leaves the network.", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "numbered", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Intelligent LLM-driven extraction. ", bold: true, font: "Arial", size: 22 }), new TextRun({ text: "Anthropic\u2019s Claude API reads the digitized text and populates rigorous, pre-defined data schemas \u2014 extracting fields like employer name, gross pay, ending balance, loan amount, and monthly debt obligations across wildly disparate document formats.", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "numbered", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Automated risk flagging. ", bold: true, font: "Arial", size: 22 }), new TextRun({ text: "The system computes derived financial metrics (DTI ratio, LTV ratio, effective tax rate) and flags anomalies against predefined thresholds \u2014 instantly triaging clean files from high-risk profiles.", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "numbered", level: 0 }, spacing: { after: 200 },
          children: [new TextRun({ text: "Natural language querying with sources. ", bold: true, font: "Arial", size: 22 }), new TextRun({ text: "Analysts \u201Cchat\u201D with documents. Ask \u201CWhat is the ending balance?\u201D and get a sourced answer citing the exact text chunk it came from, with a cosine distance score for transparency.", font: "Arial", size: 22 })],
        }),
        para("This is the DeskMate concept in action: a role-specific AI companion that handles the repetitive work so human specialists focus on complex decision-making."),

        // ── 4. What the MVP Does Today ──
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. What the MVP Does Today")] }),
        para("The following capabilities are fully implemented and operational in the current codebase. The entire stack runs via a single docker-compose up --build command."),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Supported Document Types")] }),

        // Document types table
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2000, 4360, 3000],
          rows: [
            new TableRow({ children: [
              headerCell("Document Type", 2000),
              headerCell("Extracted Fields", 4360),
              headerCell("Derived Metrics", 3000),
            ]}),
            new TableRow({ children: [
              bodyCell("Bank Statement", 2000, { bold: true }),
              bodyCell("Account number, holder name, statement date, total deposits, total withdrawals, ending balance", 4360),
              bodyCell("Deposit snapshot (income proxy)", 3000),
            ]}),
            new TableRow({ children: [
              bodyCell("Loan Application", 2000, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("Applicant name, SSN, loan amount, property value, purpose, employment status, credit score, monthly gross income, monthly debt payments", 4360, { shading: LIGHT_GRAY }),
              bodyCell("DTI ratio, LTV ratio", 3000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("Pay Stub", 2000, { bold: true }),
              bodyCell("Employee name, employer name, pay period dates, gross pay, net pay, YTD gross, taxes withheld", 4360),
              bodyCell("Effective tax rate, monthly income proxy", 3000),
            ]}),
          ],
        }),

        new Paragraph({ spacing: { before: 200 } }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Automated Risk Flags")] }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "DTI > 43%", bold: true, font: "Arial", size: 22 }), new TextRun({ text: " \u2014 High debt-to-income risk (loan applications)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "LTV > 80%", bold: true, font: "Arial", size: 22 }), new TextRun({ text: " \u2014 PMI warning (loan applications)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Tax rate < 5% or > 50%", bold: true, font: "Arial", size: 22 }), new TextRun({ text: " \u2014 Unusual withholding, investigate (pay stubs)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 200 },
          children: [new TextRun({ text: "Withdrawals > deposits", bold: true, font: "Arial", size: 22 }), new TextRun({ text: " \u2014 Negative cash flow alert (bank statements)", font: "Arial", size: 22 })],
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("RAG Query Engine")] }),
        para("Documents are chunked, embedded via OpenAI text-embedding-3-small (1536 dimensions), and indexed into PostgreSQL with pgvector (HNSW index). When an analyst submits a question, the system retrieves the top 5 most relevant chunks via cosine similarity search, synthesizes an answer through the Claude API, and displays the exact source chunks alongside the response for full auditability."),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Architecture Summary")] }),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2200, 3160, 4000],
          rows: [
            new TableRow({ children: [
              headerCell("Service", 2200),
              headerCell("Technology", 3160),
              headerCell("Role", 4000),
            ]}),
            new TableRow({ children: [
              bodyCell("Go API Gateway", 2200, { bold: true }),
              bodyCell("Go 1.23, Chi, zerolog", 3160),
              bodyCell("Routing, auth, request IDs, DB reads", 4000),
            ]}),
            new TableRow({ children: [
              bodyCell("Ingestion Service", 2200, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("Python, FastAPI, PaddleOCR", 3160, { shading: LIGHT_GRAY }),
              bodyCell("OCR, document classification", 4000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("Extraction Service", 2200, { bold: true }),
              bodyCell("Python, FastAPI, Claude API, OpenAI", 3160),
              bodyCell("Field extraction, embeddings, indexing", 4000),
            ]}),
            new TableRow({ children: [
              bodyCell("RAG Service", 2200, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("Python, FastAPI, Claude API, pgvector", 3160, { shading: LIGHT_GRAY }),
              bodyCell("Semantic search, answer synthesis", 4000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("Demo UI", 2200, { bold: true }),
              bodyCell("Streamlit", 3160),
              bodyCell("Upload, view extractions, query", 4000),
            ]}),
            new TableRow({ children: [
              bodyCell("Database", 2200, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("PostgreSQL 16 + pgvector", 3160, { shading: LIGHT_GRAY }),
              bodyCell("Single source of truth", 4000, { shading: LIGHT_GRAY }),
            ]}),
          ],
        }),

        new Paragraph({ spacing: { before: 200 } }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Known MVP Constraints")] }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Single concurrent user (demo-scoped Streamlit interface)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Synchronous processing pipeline (OCR blocks the worker)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "Polling-based status updates (UI polls every 2 seconds)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "API key authentication only (no OAuth2/RBAC)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [new TextRun({ text: "No PII redaction (raw OCR text stored in database)", font: "Arial", size: 22 })],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 200 },
          children: [new TextRun({ text: "No batch processing (one document at a time)", font: "Arial", size: 22 })],
        }),

        // ── 5. Business Value Metrics ──
        new Paragraph({ children: [new PageBreak()] }),
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. Business Value Metrics")] }),

        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2200, 2200, 2200, 2760],
          rows: [
            new TableRow({ children: [
              headerCell("Metric", 2200),
              headerCell("Legacy Processing", 2200),
              headerCell("FinDocIQ", 2200),
              headerCell("Basis", 2760),
            ]}),
            new TableRow({ children: [
              bodyCell("Data entry time per file", 2200, { bold: true }),
              bodyCell("15\u201325 minutes", 2200),
              bodyCell("< 30 seconds", 2200),
              bodyCell("Measured: OCR (3\u20138s/page) + extraction + embedding + indexing", 2760),
            ]}),
            new TableRow({ children: [
              bodyCell("Analyst capacity", 2200, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("20\u201330 files/day", 2200, { shading: LIGHT_GRAY }),
              bodyCell("60\u201390+ files/day", 2200, { shading: LIGHT_GRAY }),
              bodyCell("Derived: 85% time reduction frees analysts to review 3x more files", 2760, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("Extraction accuracy", 2200, { bold: true }),
              bodyCell("Prone to human fatigue errors", 2200),
              bodyCell("High accuracy via deterministic LLM (temp 0)", 2200),
              bodyCell("Architectural: strict JSON schemas; no benchmarks run on MVP", 2760),
            ]}),
            new TableRow({ children: [
              bodyCell("Cycle impact", 2200, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("30\u201360 day origination average", 2200, { shading: LIGHT_GRAY }),
              bodyCell("Projected 25\u201375% reduction", 2200, { shading: LIGHT_GRAY }),
              bodyCell("Industry projection for AI-augmented pipelines", 2760, { shading: LIGHT_GRAY }),
            ]}),
          ],
        }),

        new Paragraph({ spacing: { before: 300 } }),
        multiPara([
          { text: "85% reduction in manual data entry time. ", bold: true, size: 24, color: DARK_BLUE },
          { text: "The core metric. Converting 15\u201325 minutes of human labor per document into under 30 seconds of automated processing." },
        ]),
        multiPara([
          { text: "3x capacity multiplier. ", bold: true, size: 24, color: DARK_BLUE },
          { text: "By removing the data-entry bottleneck, an analyst can oversee 3x more files per day without the BPO incurring linear headcount costs." },
        ]),
        multiPara([
          { text: "< 30 seconds processing. ", bold: true, size: 24, color: DARK_BLUE },
          { text: "From document upload to fully structured extraction, database insertion, and vector indexing. Note: PaddleOCR has a one-time cold-start of 15\u201330 seconds on first call; subsequent pages process at 3\u20138 seconds each." },
        ]),

        // ── 6. Force Multiplier ──
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. The Engineering Force Multiplier")] }),
        para("A critical aspect of this MVP is how it was built. Orchestrating OCR, vector databases, RAG, a Go API gateway, and a Python microservices backend typically takes an engineering pod weeks or months."),
        multiPara([
          { text: "FinDocIQ was architected and deployed in 48 hours.", bold: true, size: 24, color: DARK_BLUE },
        ], { after: 300 }),
        para("This was achieved by leveraging agentic AI engineering workflows \u2014 specifically Anthropic\u2019s Claude Code operating with the Model Context Protocol (MCP). During the build:"),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [
            new TextRun({ text: "PostgreSQL MCP server ", bold: true, font: "Arial", size: 22 }),
            new TextRun({ text: "gave the AI agent live database access to inspect schemas, write migrations, and verify data insertion autonomously.", font: "Arial", size: 22 }),
          ],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 100 },
          children: [
            new TextRun({ text: "Bash/Shell MCP server ", bold: true, font: "Arial", size: 22 }),
            new TextRun({ text: "provided persistent terminal access for running test suites, reading stack traces, and iteratively refactoring code until all tests passed.", font: "Arial", size: 22 }),
          ],
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 }, spacing: { after: 200 },
          children: [
            new TextRun({ text: "Custom Skills ", bold: true, font: "Arial", size: 22 }),
            new TextRun({ text: "encapsulated complex, multi-step procedures (e.g., adding a new document type requires updating Pydantic models, SQL migrations, Go API routes, and tests) into single, repeatable commands \u2014 guaranteeing consistency across the codebase.", font: "Arial", size: 22 }),
          ],
        }),
        para("This proves the force multiplier argument: the technical complexities of AI pipelines are highly manageable. nuDesk can rapidly own its proprietary AI ecosystem rather than relying on expensive, rigid third-party SaaS vendors."),

        // ── 7. Strategic Alignment ──
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("7. Strategic Alignment with nuDesk")] }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("This is a DeskMate Prototype")] }),
        para("nuDesk\u2019s DeskMates are described as \u201Cintelligent, role-specific digital companions\u201D that \u201Chandle repetitive, time-consuming tasks like data entry, lead follow-ups, and reporting.\u201D FinDocIQ is exactly that \u2014 but for document-heavy workflows in credit operations, KYC, and underwriting."),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Internal Infrastructure, Not a Competing Product")] }),
        para("FinDocIQ is positioned as proprietary infrastructure for nuDesk, not a SaaS product competing in the open market. The same architecture serves any role where the bottleneck is unstructured documents: underwriting desks, KYC analysts, compliance reviewers, loan processors."),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Business-First, Not Tech-First")] }),
        para("The framing is always ROI: hours saved per analyst, error rates reduced, processing time cut. The technology is the \u201Chow,\u201D never the headline. This resonates with operators and investors who think in unit economics."),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Extensible by Design")] }),
        para("Every component is a future product surface. What the MVP demonstrates today becomes the foundation for multi-tenant SaaS, per-lender fine-tuning, compliance audit trails, and CRM integrations."),

        // ── 8. Roadmap ──
        new Paragraph({ children: [new PageBreak()] }),
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("8. Roadmap: From MVP to Enterprise")] }),
        para("The following capabilities are not implemented in the current MVP. They represent the natural evolution from prototype to production.", { italics: true }),

        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2400, 3960, 3000],
          rows: [
            new TableRow({ children: [
              headerCell("Capability", 2400),
              headerCell("Description", 3960),
              headerCell("Business Value", 3000),
            ]}),
            new TableRow({ children: [
              bodyCell("Multi-tenancy & per-lender schemas", 2400, { bold: true }),
              bodyCell("Row-level security, per-client extraction configs, isolated RAG indexes", 3960),
              bodyCell("White-label or license as standalone product; new revenue stream", 3000),
            ]}),
            new TableRow({ children: [
              bodyCell("Compliance audit trails", 2400, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("Log every extraction, query, and decision with timestamps, model versions, confidence scores", 3960, { shading: LIGHT_GRAY }),
              bodyCell("Exportable for CFPB/HMDA audits; major enterprise differentiator", 3000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("CRM & LOS integrations", 2400, { bold: true }),
              bodyCell("Connect to Encompass, Salesforce, HubSpot via workflow automation", 3960),
              bodyCell("Auto-populate CRM records; close the loop with existing tools", 3000),
            ]}),
            new TableRow({ children: [
              bodyCell("Fraud & anomaly detection", 2400, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("ML layer for income inconsistency flags, document tampering, cross-document verification", 3960, { shading: LIGHT_GRAY }),
              bodyCell("Catch W-2 vs. bank statement income mismatches automatically", 3000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("Async processing", 2400, { bold: true }),
              bodyCell("Job queue (Celery/Redis) replacing synchronous HTTP flow", 3960),
              bodyCell("Handle enterprise volume without timeouts", 3000),
            ]}),
            new TableRow({ children: [
              bodyCell("Production auth", 2400, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("OAuth2, JWT session management, RBAC", 3960, { shading: LIGHT_GRAY }),
              bodyCell("Mandatory for multi-user, multi-tenant deployment", 3000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("PII redaction", 2400, { bold: true }),
              bodyCell("ML-based detection and masking before database insertion", 3960),
              bodyCell("Regulatory compliance for financial data", 3000),
            ]}),
            new TableRow({ children: [
              bodyCell("Voice-first query", 2400, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("Whisper transcription to RAG to TTS", 3960, { shading: LIGHT_GRAY }),
              bodyCell("Hands-free querying for dual-monitor analysts", 3000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("On-premise deployment", 2400, { bold: true }),
              bodyCell("Ollama for LLMs, local PaddleOCR, no cloud APIs", 3960),
              bodyCell("Zero data egress for highly regulated clients", 3000),
            ]}),
          ],
        }),

        // ── 9. Go-to-Market Positioning ──
        new Paragraph({ spacing: { before: 200 } }),
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("9. Go-to-Market Positioning")] }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Talking Points for Executive Stakeholders")] }),

        multiPara([
          { text: "Open with the problem, not the tech. ", bold: true, color: DARK_BLUE },
          { text: "\u201CA loan ops analyst at a mid-size lender processes 20\u201330 files a day. Each file takes 15\u201325 minutes of manual data entry. That is over 6 hours a day of repetitive, error-prone work. FinDocIQ reduces the data extraction component to under 30 seconds per file.\u201D", italics: true },
        ]),
        multiPara([
          { text: "Connect to nuDesk\u2019s DeskMates explicitly. ", bold: true, color: DARK_BLUE },
          { text: "\u201CThis is a DeskMate prototype for document-heavy roles. The same architecture serves underwriting desks, KYC analysts, compliance reviewers \u2014 any role where the bottleneck is unstructured documents.\u201D", italics: true },
        ]),
        multiPara([
          { text: "Show the SaaS path. ", bold: true, color: DARK_BLUE },
          { text: "\u201CAdd multi-tenancy and per-lender fine-tuning, and this becomes a standalone product. The Go API is stateless and horizontally scalable. The data pipeline is schema-agnostic \u2014 adding a new document type is a single command.\u201D", italics: true },
        ]),
        multiPara([
          { text: "The force multiplier closing. ", bold: true, color: DARK_BLUE },
          { text: "\u201CI built this end-to-end in 48 hours \u2014 OCR, embeddings, RAG, a production API, and a working UI. The technical complexity is solved. What matters at nuDesk is choosing the right problems to solve and moving fast. That is what I am here to do.\u201D", italics: true },
        ]),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Presentation Flow")] }),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2000, 1360, 6000],
          rows: [
            new TableRow({ children: [
              headerCell("Phase", 2000),
              headerCell("Time", 1360),
              headerCell("Focus", 6000),
            ]}),
            new TableRow({ children: [
              bodyCell("Business Hook", 2000, { bold: true }),
              bodyCell("0\u20135 min", 1360),
              bodyCell("The pain: 6+ hours/day of manual data entry. Position FinDocIQ as the DeskMate that compresses this to minutes.", 6000),
            ]}),
            new TableRow({ children: [
              bodyCell("Live Demo", 2000, { bold: true, shading: LIGHT_GRAY }),
              bodyCell("5\u201320 min", 1360, { shading: LIGHT_GRAY }),
              bodyCell("Upload a synthetic PDF. Show extraction, risk flags, RAG query with sources. Then demonstrate Claude Code + MCP building a feature live.", 6000, { shading: LIGHT_GRAY }),
            ]}),
            new TableRow({ children: [
              bodyCell("Enterprise Roadmap", 2000, { bold: true }),
              bodyCell("20\u201330 min", 1360),
              bodyCell("Transition from MVP constraints to the productization path. Proactively address limitations and map out engineering solutions.", 6000),
            ]}),
          ],
        }),
      ],
    },
  ],
});

// ── Generate ──
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("D:/Repos/nudesk-mvp/docs/BUSS_DETAILS.docx", buffer);
  console.log("BUSS_DETAILS.docx generated successfully");
});
