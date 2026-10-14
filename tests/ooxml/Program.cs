// Program.cs
// 2026-10-14
// Version: v1.0.0
//
// PURPOSE:
// Validates Office files (.pptx, .docx) with Microsoft's Open XML SDK, for
// Office 2007, 2016, and Microsoft 365. Prints each problem and exits with
// 1 when there is any. Usage: OoxmlValidator FILE...
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Validation;

int problems = 0;
foreach (var path in args)
{
    using OpenXmlPackage doc = Path.GetExtension(path).ToLowerInvariant() switch
    {
        ".pptx" => PresentationDocument.Open(path, false),
        ".docx" => WordprocessingDocument.Open(path, false),
        _ => throw new ArgumentException($"Not a .pptx or .docx file: {path}"),
    };
    foreach (var version in new[] { FileFormatVersions.Office2007, FileFormatVersions.Office2016,
                                    FileFormatVersions.Microsoft365 })
    {
        var errors = new OpenXmlValidator(version).Validate(doc).ToList();
        Console.WriteLine($"{Path.GetFileName(path)} [{version}]: {errors.Count} problem(s)");
        foreach (var e in errors.Take(25))
            Console.WriteLine($"  {e.Part?.Uri} {e.Path?.XPath}: {e.Description}");
        problems += errors.Count;
    }
}
return problems == 0 ? 0 : 1;
