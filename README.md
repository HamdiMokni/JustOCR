# PDF OCR Application

A user-friendly desktop application for performing OCR (Optical Character Recognition) on PDF files. This application provides a graphical interface for converting scanned PDFs into searchable documents using OCR technology.

## Features

- 🖼️ **User-Friendly Interface**: Clean and intuitive GUI built with tkinter
- 🌍 **Multi-Language Support**: OCR support for multiple languages including:
  - English
  - French
  - Arabic
  - Spanish
  - German
  - Italian
  - Portuguese
  - Russian
  - Chinese (Simplified & Traditional)
  - Japanese
- 📄 **Flexible OCR Modes**:
  - Skip pages with text (recommended)
  - Force OCR on all pages
  - Redo OCR on pages with text
- 🎯 **Quality Control**:
  - Adjustable PDF output quality (High, Medium, Low)
  - Configurable image compression settings
- 🔍 **Debug Features**:
 - Comprehensive logging system
 - System information collection
 - Dependency testing
 - Detailed error reporting
- Automatic chunking for large PDFs

## Prerequisites

Before using this application, ensure you have the following installed:

1. **Python 3.7 or higher**
2. **Required Python packages**:
   ```bash
   pip install ocrmypdf PyPDF2
   ```
3. **System Dependencies**:
   - Tesseract OCR
   - Ghostscript
   - ocrmypdf

## Installation

1. Clone or download this repository
2. Install the required Python package:
   ```bash
   pip install ocrmypdf
   ```
3. Install system dependencies:

   **Windows**:
   - Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - Download and install [Ghostscript](https://www.ghostscript.com/releases/gsdnld.html)
   - Add both to your system PATH

   **Linux**:
   ```bash
   sudo apt-get install tesseract-ocr
   sudo apt-get install ghostscript
   ```

   **macOS**:
   ```bash
   brew install tesseract
   brew install ghostscript
   ```

## Usage

1. Launch the application:
   ```bash
   python PDF_OCR.py
   ```

2. Using the application:
   - Click "Browse" to select a PDF file
   - Choose the desired language for OCR
   - Select the OCR mode
   - Choose the output PDF quality
   - Click "Process OCR" to start the conversion
   - Monitor progress in the output log
   - When complete, choose to open the output folder

## OCR Modes Explained

1. **Skip pages with text (recommended)**:
   - Only processes pages without existing text
   - Fastest and safest option
   - Best for scanned documents

2. **Force OCR on all pages**:
   - Processes all pages regardless of existing text
   - Use when existing text is poor quality
   - Helps avoid Ghostscript version issues

3. **Redo OCR on pages with text**:
   - Removes existing text and replaces with new OCR
   - Improves searchable text quality
   - Best for documents with poor existing OCR

## Troubleshooting

### Common Issues

1. **Ghostscript Version Issues**:
   - If using Ghostscript 10.0.0 through 10.02.0, use "Force OCR" mode
   - Consider downgrading to Ghostscript 9.56 for better compatibility

2. **Permission Errors**:
   - Run the application as Administrator
   - Ensure the PDF isn't open in another program
   - Check antivirus settings

3. **Font Loading Errors**:
   - Use "Force OCR on all pages" mode
   - Update system fonts
   - Restart the application

4. **Large PDF Timeouts**:
   - The app automatically splits very large PDFs into chunks
   - Ensure there is enough disk space for temporary files
   - Try reducing the PDF quality setting if processing is slow

### Debug Features

- Use the "Test Dependencies" button to verify all required components
- Check the debug log for detailed error information
- Export debug reports for troubleshooting

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [ocrmypdf](https://github.com/jbarlow83/OCRmyPDF)
- Uses [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- Powered by [Ghostscript](https://www.ghostscript.com/) 