# TypeSafe AI PDF test

This console app extracts text from the PDFs in `data/` and sends each selected document to TypeSafe AI with three typed questions:

The Harry Potter-themed PDFs in `data/` are synthetic test data for evaluating the TypeSafe AI workflow. They contain original thematic commentary and summaries, not complete copyrighted books or copied book text.

- Is the document thematically coherent?
- What is its primary analytical focus?
- How original does the commentary appear?

## Run

Set the API key in the current PowerShell session:

```powershell
$env:TYPESAFE_API_KEY = "your-key"
```

Run a five-document smoke test:

```powershell
dotnet run --project .\TypeSafeJev.csproj
```

Run every PDF in `data/`:

```powershell
dotnet run --project .\TypeSafeJev.csproj -- --all
```

Use a custom number of documents with `--limit`, for example `--limit 10`. Results are written to `typesafe-results.json`.

## Processing flow

```mermaid
flowchart LR
	A[data/*.pdf] --> B[Extract PDF text]
	B --> C[Send text to TypeSafe AI]
	C --> D[Typed questions]
	D --> E[Coherence probability]
	D --> F[Primary focus label]
	D --> G[Originality score]
	E --> H[typesafe-results.json]
	F --> H
	G --> H
```

## Score rubric

```mermaid
flowchart LR
	L[0: low] --> M[1: moderate] --> H[2: high]
	M -. weighted result .-> R[Example: 1.6 means between moderate and high]
```