using System.Text.Json;
using TypeSafe;
using UglyToad.PdfPig;

const int DefaultDocumentLimit = 5;
const int MaxInputCharacters = 24_000;

var dataDirectory = Path.Combine(AppContext.BaseDirectory, "data");
if (!Directory.Exists(dataDirectory))
{
    dataDirectory = Path.Combine(Directory.GetCurrentDirectory(), "data");
}

var allDocuments = args.Contains("--all", StringComparer.OrdinalIgnoreCase);
var requestedLimit = ReadLimit(args);
var documentLimit = allDocuments ? int.MaxValue : requestedLimit ?? DefaultDocumentLimit;
var pdfFiles = Directory.GetFiles(dataDirectory, "*.pdf")
    .OrderBy(path => path, StringComparer.OrdinalIgnoreCase)
    .Take(documentLimit)
    .ToArray();

if (pdfFiles.Length == 0)
{
    Console.Error.WriteLine($"No PDF files found in {dataDirectory}.");
    return 1;
}

if (string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("TYPESAFE_API_KEY")))
{
    Console.Error.WriteLine("Set TYPESAFE_API_KEY before running the test.");
    Console.Error.WriteLine("PowerShell: $env:TYPESAFE_API_KEY = \"your-key\"");
    return 2;
}

var outputPath = Path.Combine(Directory.GetCurrentDirectory(), "typesafe-results.json");
using var client = new TypeSafeClient();
var results = new List<DocumentResult>();

Console.WriteLine($"Testing {pdfFiles.Length} of {Directory.GetFiles(dataDirectory, "*.pdf").Length} PDFs from {dataDirectory}");

foreach (var pdfFile in pdfFiles)
{
    try
    {
        var text = ExtractText(pdfFile);
        var questions = new QuestionSet
        {
            new NoulQuestion("is_thematically_coherent", "Does this document present a coherent literary analysis rather than random or unrelated text?"),
            new ChoiceQuestion("primary_focus", "What is the primary focus of this document?", ["character", "setting", "ethics", "relationships", "narrative structure"]),
            new ScoreQuestion("originality", "How strongly does the document appear to contain original commentary rather than reproduced source text?", ["low", "moderate", "high"]),
        };

        var answer = await client.SystemOneAsync(text, questions);
        var result = new DocumentResult(
            Path.GetFileName(pdfFile),
            text.Length,
            answer.Noul("is_thematically_coherent").Probability,
            answer.Choice("primary_focus").Label,
            answer.Score("originality").Score,
            null);
        results.Add(result);
        Console.WriteLine($"OK   {result.FileName} | coherent={result.CoherentProbability:F2} | focus={result.PrimaryFocus} | originality={result.OriginalityScore:F2}");
    }
    catch (Exception exception)
    {
        var result = new DocumentResult(Path.GetFileName(pdfFile), 0, null, null, null, exception.Message);
        results.Add(result);
        Console.WriteLine($"FAIL {result.FileName} | {exception.Message}");
    }
}

var json = JsonSerializer.Serialize(results, new JsonSerializerOptions { WriteIndented = true });
await File.WriteAllTextAsync(outputPath, json);
Console.WriteLine($"Results written to {outputPath}");
return results.Any(result => result.Error is not null) ? 3 : 0;

static int? ReadLimit(string[] arguments)
{
    var index = Array.FindIndex(arguments, argument => argument.Equals("--limit", StringComparison.OrdinalIgnoreCase));
    if (index < 0 || index + 1 >= arguments.Length || !int.TryParse(arguments[index + 1], out var limit) || limit < 1)
    {
        return null;
    }

    return limit;
}

static string ExtractText(string pdfFile)
{
    using var document = PdfDocument.Open(pdfFile);
    var text = string.Join(Environment.NewLine, document.GetPages().Select(page => page.Text));
    return text.Length <= MaxInputCharacters ? text : text[..MaxInputCharacters];
}

sealed record DocumentResult(
    string FileName,
    int InputCharacters,
    double? CoherentProbability,
    string? PrimaryFocus,
    double? OriginalityScore,
    string? Error);