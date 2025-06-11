import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import threading
import logging
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter

class PDFOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF OCR Application")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Debug variables - always enabled
        self.debug_mode = tk.BooleanVar(value=True)
        self.log_to_file = tk.BooleanVar(value=True)
        self.debug_info = {}
        
        # Setup logging
        self.setup_logging()
        
        # Variables
        self.selected_file = tk.StringVar()
        self.selected_language = tk.StringVar(value="eng")
        self.progress_var = tk.DoubleVar()
        self.ocr_mode = tk.StringVar(value="skip_text")  # Default mode
        # PDF Quality options
        self.pdf_quality = tk.StringVar(value="Medium")
        self.pdf_quality_options = {
            "High": {"jpeg_quality": "95", "optimize": "0"},
            "Medium": {"jpeg_quality": "85", "optimize": "1"},
            "Low": {"jpeg_quality": "60", "optimize": "2"}
        }
        # Language options
        self.languages = {
            "English": "eng",
            "French": "fra",
            "Arabic": "ara",
            "Spanish": "spa",
            "German": "deu",
            "Italian": "ita",
            "Portuguese": "por",
            "Russian": "rus",
            "Chinese Simplified": "chi_sim",
            "Chinese Traditional": "chi_tra",
            "Japanese": "jpn"
        }

        # Large PDF handling settings
        self.large_pdf_page_threshold = 100  # number of pages to trigger chunking
        self.chunk_size = 50  # pages per OCR chunk
        
        self.setup_ui()
        self.debug_system_info()
        
    def setup_logging(self):
        """Setup logging configuration with enhanced error handling"""
        try:
            log_filename = f"pdf_ocr_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            # Create logs directory if it doesn't exist
            log_dir = Path("logs")
            try:
                log_dir.mkdir(exist_ok=True)
            except PermissionError:
                # Fallback to user's home directory if logs directory creation fails
                log_dir = Path.home() / "pdf_ocr_logs"
                log_dir.mkdir(exist_ok=True)
                self.log_message(f"Created logs directory in user's home: {log_dir}")
            
            self.log_file_path = log_dir / log_filename
            
            # Configure logging with UTF-8 encoding and error handling
            try:
                logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(self.log_file_path, encoding='utf-8', mode='a'),
                        logging.StreamHandler(sys.stdout)
                    ]
                )
                
                self.logger = logging.getLogger(__name__)
                self.logger.info("PDF OCR Application started with debug logging")
                self.logger.info(f"Log file location: {self.log_file_path}")
                
            except PermissionError:
                # Fallback to console-only logging if file writing fails
                logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)]
                )
                self.logger = logging.getLogger(__name__)
                self.logger.warning("Could not create log file. Logging to console only.")
                self.log_to_file.set(False)
                
        except Exception as e:
            # Last resort fallback for logging setup
            print(f"Critical error in logging setup: {e}")
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Failed to setup logging: {e}")
            self.log_to_file.set(False)
        
    def debug_system_info(self):
        """Collect and log system information for debugging"""
        try:
            import platform
            import shutil
            
            self.debug_info = {
                "timestamp": datetime.now().isoformat(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "system": platform.system(),
                "release": platform.release(),
                "tkinter_version": tk.TkVersion,
                "working_directory": os.getcwd(),
                "script_location": os.path.abspath(__file__),
                "ocrmypdf_available": bool(shutil.which("ocrmypdf")),
                "gs_available": bool(shutil.which("gs") or shutil.which("gswin32c") or shutil.which("gswin64c")),
                "tesseract_available": bool(shutil.which("tesseract")),
                "environment_vars": {
                    "PATH": os.environ.get("PATH", ""),
                    "TESSDATA_PREFIX": os.environ.get("TESSDATA_PREFIX", "Not set"),
                    "GHOSTSCRIPT_PATH": os.environ.get("GHOSTSCRIPT_PATH", "Not set")
                }
            }
            
            # Check versions if tools are available
            if self.debug_info["ocrmypdf_available"]:
                try:
                    result = subprocess.run(["ocrmypdf", "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    self.debug_info["ocrmypdf_version"] = result.stdout.strip()
                except Exception as e:
                    self.debug_info["ocrmypdf_version"] = f"Error getting version: {e}"
            
            if self.debug_info["gs_available"]:
                try:
                    gs_cmd = "gs"
                    if os.name == 'nt':  # Windows
                        gs_cmd = shutil.which("gswin64c") or shutil.which("gswin32c") or "gs"
                    result = subprocess.run([gs_cmd, "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    self.debug_info["ghostscript_version"] = result.stdout.strip()
                except Exception as e:
                    self.debug_info["ghostscript_version"] = f"Error getting version: {e}"
            
            if self.debug_info["tesseract_available"]:
                try:
                    result = subprocess.run(["tesseract", "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    self.debug_info["tesseract_version"] = result.stdout.split('\n')[0]
                except Exception as e:
                    self.debug_info["tesseract_version"] = f"Error getting version: {e}"
            
            self.logger.info(f"System debug info collected: {self.debug_info}")
            
        except Exception as e:
            self.logger.error(f"Error collecting system info: {e}")
            self.debug_info["error"] = str(e)
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF OCR Application", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection
        ttk.Label(main_frame, text="Select PDF File:").grid(row=1, column=0, 
                                                           sticky=tk.W, pady=5)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), 
                       pady=5, padx=(10, 0))
        file_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(file_frame, textvariable=self.selected_file, 
                                   state="readonly")
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(file_frame, text="Browse", 
                  command=self.browse_file).grid(row=0, column=1)
        
        # Language selection
        ttk.Label(main_frame, text="Select Language:").grid(row=2, column=0, 
                                                           sticky=tk.W, pady=5)
        
        language_combo = ttk.Combobox(main_frame, textvariable=self.selected_language,
                                     values=list(self.languages.keys()),
                                     state="readonly", width=20)
        language_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        language_combo.set("English")
        
        # PDF Quality selection
        ttk.Label(main_frame, text="Output PDF Quality:").grid(row=3, column=0, sticky=tk.W, pady=5)
        quality_combo = ttk.Combobox(main_frame, textvariable=self.pdf_quality,
                                    values=list(self.pdf_quality_options.keys()),
                                    state="readonly", width=20)
        quality_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        quality_combo.set("Medium")
        
        # OCR Mode selection
        ttk.Label(main_frame, text="OCR Mode:").grid(row=4, column=0, 
                                                   sticky=tk.W, pady=5)
        
        ocr_mode_frame = ttk.Frame(main_frame)
        ocr_mode_frame.grid(row=4, column=1, columnspan=2, sticky=tk.W, 
                           pady=5, padx=(10, 0))
        
        # OCR mode options
        self.ocr_modes = {
            "Skip pages with text (recommended)": "skip_text",
            "Force OCR on all pages": "force_ocr", 
            "Redo OCR on pages with text": "redo_ocr"
        }
        
        ocr_mode_combo = ttk.Combobox(ocr_mode_frame, textvariable=self.ocr_mode,
                                     values=list(self.ocr_modes.keys()),
                                     state="readonly", width=35)
        ocr_mode_combo.grid(row=0, column=0)
        ocr_mode_combo.set("Skip pages with text (recommended)")
        
        # Help button for OCR modes
        help_button = ttk.Button(ocr_mode_frame, text="?", width=3,
                               command=self.show_ocr_mode_help)
        help_button.grid(row=0, column=1, padx=(5, 0))
        
        # Progress bar
        ttk.Label(main_frame, text="Progress:").grid(row=5, column=0, 
                                                   sticky=tk.W, pady=(20, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                          maximum=100, length=300)
        self.progress_bar.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E),
                              pady=(20, 5), padx=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to process files")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(20, 0))
        
        self.process_button = ttk.Button(button_frame, text="Process OCR", 
                                       command=self.start_ocr_process,
                                       style="Accent.TButton")
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear", 
                  command=self.clear_fields).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Test Dependencies", 
                  command=self.test_dependencies).pack(side=tk.LEFT)
        
        # Output text area
        ttk.Label(main_frame, text="Output Log:").grid(row=8, column=0, 
                                                     sticky=(tk.W, tk.N), pady=(20, 5))
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=8, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S),
                       pady=(20, 0), padx=(10, 0))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.output_text = tk.Text(text_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, 
                                 command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure main_frame row weights
        main_frame.rowconfigure(8, weight=1)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.selected_file.set(filename)
            self.log_message(f"Selected file: {os.path.basename(filename)}")
            
            # Debug file information
            if self.debug_mode.get():
                try:
                    file_stat = os.stat(filename)
                    file_size = file_stat.st_size
                    self.debug_log(f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                    self.debug_log(f"File permissions: {oct(file_stat.st_mode)}")
                    self.debug_log(f"File path: {filename}")
                except Exception as e:
                    self.debug_log(f"Error getting file info: {e}")
    
    def clear_fields(self):
        self.selected_file.set("")
        self.selected_language.set("English")
        self.ocr_mode.set("Skip pages with text (recommended)")
        self.progress_var.set(0)
        self.output_text.delete(1.0, tk.END)
        self.status_label.config(text="Ready to process files")
        self.process_button.config(state="normal")
        
        if self.debug_mode.get():
            self.debug_log("Fields cleared")
    
    def show_ocr_mode_help(self):
        help_text = """OCR Mode Options:

• Skip pages with text (recommended): 
  Only processes pages that don't already have text.
  This is the fastest and safest option.
  Uses --output-type pdf to avoid Ghostscript bugs.

• Force OCR on all pages: 
  Ignores existing text and runs OCR on all pages.
  Use this if existing text is poor quality or to avoid
  Ghostscript version issues.

• Redo OCR on pages with text: 
  Removes existing text and replaces it with OCR.
  Use this to improve searchable text quality.
  Uses --output-type pdf to avoid Ghostscript bugs.

Note: If you encounter Ghostscript errors, try 'Force OCR' mode."""
        
        messagebox.showinfo("OCR Mode Help", help_text)
    
    def show_system_info(self):
        """Display system information dialog"""
        info_text = f"""System Information:

Platform: {self.debug_info.get('platform', 'Unknown')}
Python Version: {self.debug_info.get('python_version', 'Unknown')}
Architecture: {self.debug_info.get('architecture', 'Unknown')}
System: {self.debug_info.get('system', 'Unknown')}

Tool Availability:
• ocrmypdf: {'✓' if self.debug_info.get('ocrmypdf_available') else '✗'}
• Ghostscript: {'✓' if self.debug_info.get('gs_available') else '✗'}
• Tesseract: {'✓' if self.debug_info.get('tesseract_available') else '✗'}

Versions:
• ocrmypdf: {self.debug_info.get('ocrmypdf_version', 'Not available')}
• Ghostscript: {self.debug_info.get('ghostscript_version', 'Not available')}
• Tesseract: {self.debug_info.get('tesseract_version', 'Not available')}

Working Directory: {self.debug_info.get('working_directory', 'Unknown')}
Log File: {self.log_file_path}"""
        
        messagebox.showinfo("System Information", info_text)
    
    def export_debug_report(self):
        """Export comprehensive debug report"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = Path(f"debug_report_{timestamp}.txt")
            
            with open(report_file, 'w') as f:
                f.write("PDF OCR Application Debug Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                
                f.write("SYSTEM INFORMATION:\n")
                f.write("-" * 20 + "\n")
                for key, value in self.debug_info.items():
                    if key != "environment_vars":
                        f.write(f"{key}: {value}\n")
                
                f.write("\nENVIRONMENT VARIABLES:\n")
                f.write("-" * 20 + "\n")
                for key, value in self.debug_info.get("environment_vars", {}).items():
                    f.write(f"{key}: {value[:200]}{'...' if len(str(value)) > 200 else ''}\n")
                
                f.write("\nAPPLICATION LOG:\n")
                f.write("-" * 20 + "\n")
                f.write(self.output_text.get(1.0, tk.END))
            
            messagebox.showinfo("Debug Report", f"Debug report exported to:\n{report_file.absolute()}")
            self.log_message(f"Debug report exported: {report_file}")
            
        except Exception as e:
            self.log_message(f"Error exporting debug report: {e}")
            messagebox.showerror("Error", f"Failed to export debug report: {e}")
    
    def test_dependencies(self):
        """Test all required dependencies"""
        self.log_message("Testing dependencies...")
        self.status_label.config(text="Testing dependencies...")
        
        def test_thread():
            try:
                # Test ocrmypdf
                self.log_message("Testing ocrmypdf...")
                result = subprocess.run(["ocrmypdf", "--help"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log_message("✓ ocrmypdf is working")
                else:
                    self.log_message("✗ ocrmypdf test failed")
                
                # Test Ghostscript
                self.log_message("Testing Ghostscript...")
                gs_commands = ["gs", "gswin64c", "gswin32c"]
                gs_working = False
                
                for gs_cmd in gs_commands:
                    try:
                        result = subprocess.run([gs_cmd, "--version"], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            self.log_message(f"✓ Ghostscript is working ({gs_cmd}): {result.stdout.strip()}")
                            gs_working = True
                            break
                    except FileNotFoundError:
                        continue
                
                if not gs_working:
                    self.log_message("✗ Ghostscript not found or not working")
                
                # Test Tesseract
                self.log_message("Testing Tesseract...")
                result = subprocess.run(["tesseract", "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    self.log_message(f"✓ Tesseract is working: {version_line}")
                else:
                    self.log_message("✗ Tesseract test failed")
                
                self.log_message("Dependency testing completed!")
                self.status_label.config(text="Dependency testing completed")
                
            except Exception as e:
                self.log_message(f"Error during dependency testing: {e}")
                self.status_label.config(text="Dependency testing failed")
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def debug_log(self, message):
        """Log debug messages"""
        if self.debug_mode.get():
            debug_msg = f"[DEBUG] {message}"
            self.log_message(debug_msg)
            self.logger.debug(message)
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Replace Unicode symbols with ASCII alternatives
        message = message.replace('✗', 'X').replace('✓', 'V').replace('⚠', '!')
        formatted_message = f"[{timestamp}] {message}"
        self.output_text.insert(tk.END, f"{formatted_message}\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
        # Log to file if enabled
        if self.log_to_file.get():
            self.logger.info(message)
    
    def start_ocr_process(self):
        if not self.selected_file.get():
            messagebox.showerror("Error", "Please select a PDF file first.")
            return
        
        if not os.path.exists(self.selected_file.get()):
            messagebox.showerror("Error", "Selected file does not exist.")
            return
        
        # Disable button during processing
        self.process_button.config(state="disabled")
        
        # Start OCR in a separate thread to prevent GUI freezing
        thread = threading.Thread(target=self.process_ocr)
        thread.daemon = True
        thread.start()
    
    def process_ocr(self):
        start_time = time.time()
        
        try:
            input_file = self.selected_file.get()
            
            # Get language code
            lang_name = self.selected_language.get()
            lang_code = self.languages.get(lang_name, "eng")
            
            # Get OCR mode
            ocr_mode_name = self.ocr_mode.get()
            ocr_mode_flag = self.ocr_modes.get(ocr_mode_name, "skip_text")
            
            # Get PDF quality
            quality_name = self.pdf_quality.get()
            quality_opts = self.pdf_quality_options.get(quality_name, {"jpeg_quality": "85", "optimize": "1"})
            
            # Generate output filename
            input_path = Path(input_file)
            output_file = str(input_path.parent / f"{input_path.stem}_ocr{input_path.suffix}")
            
            self.log_message(f"Starting OCR process...")
            self.debug_log(f"Process started at: {datetime.now().isoformat()}")
            self.log_message(f"Input: {os.path.basename(input_file)}")
            self.log_message(f"Language: {lang_name} ({lang_code})")
            self.log_message(f"OCR Mode: {ocr_mode_name}")
            self.log_message(f"Output PDF Quality: {quality_name}")
            self.log_message(f"Output: {os.path.basename(output_file)}")
            
            # Debug file info
            if self.debug_mode.get():
                try:
                    file_stat = os.stat(input_file)
                    self.debug_log(f"Input file size: {file_stat.st_size:,} bytes")
                    self.debug_log(f"Available disk space: {self.get_free_space(input_path.parent):,} bytes")
                except Exception as e:
                    self.debug_log(f"Error getting file stats: {e}")
            
            self.status_label.config(text="Processing OCR...")
            self.progress_var.set(25)
            
            # Construct ocrmypdf command with robust options
            cmd = ["ocrmypdf"]
            
            # Add language
            cmd.extend(["-l", lang_code])
            
            # Add quality options
            cmd.extend([
                "--pdfa-image-compression", "jpeg",
                "--optimize", quality_opts["optimize"],
                "--jpeg-quality", quality_opts["jpeg_quality"]
            ])
            
            # Add debug verbosity if debug mode is enabled
            if self.debug_mode.get():
                cmd.extend(["-v", "1"])  # Verbose output
            
            # Check for Ghostscript version and adjust strategy
            gs_version_issue = self.check_ghostscript_version()
            
            # Add OCR mode flag with intelligent Ghostscript handling
            if gs_version_issue:
                # Force OCR mode for problematic Ghostscript versions
                cmd.append("--force-ocr")
                cmd.extend(["--output-type", "pdf"])
                self.log_message("! Auto-switched to --force-ocr due to Ghostscript version issue")
                self.debug_log("Auto-switched to --force-ocr due to GS version issue")
            else:
                if ocr_mode_flag == "force_ocr":
                    cmd.append("--force-ocr")
                    self.debug_log("Using --force-ocr mode")
                elif ocr_mode_flag == "redo_ocr":
                    cmd.append("--redo-ocr")
                    cmd.extend(["--output-type", "pdf"])
                    self.debug_log("Using --redo-ocr mode")
                else:  # skip_text (default)
                    cmd.append("--skip-text")
                    cmd.extend(["--output-type", "pdf"])
                    self.debug_log("Using --skip-text mode")
            
            # Add additional stability options for Ghostscript 10.x
            if gs_version_issue:
                cmd.extend([
                    "--skip-big", "50",  # Skip images larger than 50 megapixels
                    "--png-quality", "100",  # Use maximum PNG quality
                    "--tesseract-config", "tessedit_do_invert=0"  # Disable image inversion
                ])
            
            # Determine if file should be processed in chunks
            num_pages = self.get_pdf_page_count(input_file)
            cmd_base = cmd[:]

            if num_pages >= self.large_pdf_page_threshold:
                self.process_large_pdf(input_file, output_file, cmd_base, num_pages)
                result = subprocess.CompletedProcess(cmd_base, 0, '', '')
                process_time = time.time() - start_time
            else:
                # Add input and output files
                cmd.extend([input_file, output_file])

                # Validate command before execution
                is_valid, validation_msg = self.validate_ocr_command(cmd)
                if not is_valid:
                    raise ValueError(validation_msg)

                self.log_message(f"Running command: {' '.join(cmd)}")
                self.debug_log(f"Command length: {len(' '.join(cmd))} characters")
                self.debug_log(f"Working directory: {os.getcwd()}")

                self.progress_var.set(50)

                # Run the command with enhanced debugging and increased timeout
                process_start = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True,
                                      cwd=os.getcwd(), timeout=900)  # 15 minute timeout
                process_time = time.time() - process_start
            
            self.debug_log(f"Process execution time: {process_time:.2f} seconds")
            self.debug_log(f"Return code: {result.returncode}")
            
            if self.debug_mode.get():
                if result.stdout:
                    self.debug_log(f"STDOUT: {result.stdout[:500]}{'...' if len(result.stdout) > 500 else ''}")
                if result.stderr:
                    self.debug_log(f"STDERR: {result.stderr[:500]}{'...' if len(result.stderr) > 500 else ''}")
            
            self.progress_var.set(75)
            
            if result.returncode == 0:
                self.progress_var.set(100)
                total_time = time.time() - start_time
                self.status_label.config(text="OCR completed successfully!")
                self.log_message("V OCR process completed successfully!")
                self.log_message(f"Total processing time: {total_time:.2f} seconds")
                self.log_message(f"Output saved as: {os.path.basename(output_file)}")
                
                # Check output file
                if os.path.exists(output_file):
                    output_size = os.path.getsize(output_file)
                    self.debug_log(f"Output file size: {output_size:,} bytes")
                    
                    # Show success message with option to open output folder
                    response = messagebox.askyesno(
                        "Success", 
                        f"OCR completed successfully!\n\nOutput saved as:\n{output_file}\n\nWould you like to open the output folder?"
                    )
                    if response:
                        self.open_output_folder(output_file)
                else:
                    self.log_message("! Warning: Output file was not created")
                    
            else:
                self.progress_var.set(0)
                self.status_label.config(text="OCR process failed!")
                self.log_message("X OCR process failed!")
                
                # Enhanced error handling with specific solutions
                error_details = result.stderr if result.stderr else "Unknown error"
                
                # Log full error in debug mode
                if self.debug_mode.get():
                    self.debug_log(f"Full error output: {error_details}")
                
                if "Ghostscript" in error_details or gs_version_issue:
                    solution_msg = ("GHOSTSCRIPT VERSION ISSUE DETECTED\n\n"
                                  "Your Ghostscript version (10.01.1) has known PDF corruption bugs.\n\n"
                                  "AUTOMATIC FIX APPLIED:\n"
                                  "The app has automatically switched to 'Force OCR' mode with additional stability options.\n\n"
                                  "MANUAL SOLUTIONS (if needed):\n"
                                  "1. Downgrade to Ghostscript 9.56:\n"
                                  "   https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/tag/gs956\n"
                                  "2. Wait for Ghostscript 10.03+ update\n\n"
                                  "TRY AGAIN: The next run should work with the automatic fix!")
                    
                    self.log_message("! Ghostscript version issue detected - automatic fix applied")
                    messagebox.showinfo("Ghostscript Issue - Auto-Fix Available", solution_msg)
                    
                elif "Permission denied" in error_details:
                    solution_msg = ("PERMISSION ERROR\n\n"
                                  "Possible solutions:\n"
                                  "1. Run the app as Administrator\n"
                                  "2. Check if the PDF file is open in another program\n"
                                  "3. Try saving to a different location (like Desktop)\n"
                                  "4. Check antivirus software isn't blocking the process")
                    
                    self.log_message("! Permission denied - try running as Administrator")
                    messagebox.showerror("Permission Error", solution_msg)
                    
                elif "font" in error_details.lower() and "loading" in error_details.lower():
                    solution_msg = ("FONT LOADING ERROR\n\n"
                                  "This appears to be a font-related issue.\n\n"
                                  "Solutions:\n"
                                  "1. Use 'Force OCR on all pages' mode (bypasses font issues)\n"
                                  "2. Update your system fonts\n"
                                  "3. Restart the application")
                    
                    self.log_message("! Font loading error - try 'Force OCR' mode")
                    messagebox.showerror("Font Error", solution_msg)
                    
                else:
                    # Generic error
                    error_msg = f"OCR process failed!\n\nTechnical details:\n{error_details}"
                    messagebox.showerror("Error", error_msg)
                    
                if error_details:
                    self.log_message(f"Error details: {error_details[:200]}{'...' if len(error_details) > 200 else ''}")
                
        except ValueError as e:
            self.progress_var.set(0)
            self.status_label.config(text="Validation error!")
            self.log_message(f"✗ {str(e)}")
            messagebox.showerror("Validation Error", str(e))
            
        except subprocess.TimeoutExpired:
            self.progress_var.set(0)
            self.status_label.config(text="OCR process timed out!")
            timeout_msg = "OCR process timed out after 15 minutes.\n\nPossible causes:\n• Very large PDF file\n• System resource limitations\n• Ghostscript compatibility issues\n\nTry using 'Force OCR' mode or processing a smaller file."
            self.log_message("X OCR process timed out")
            self.debug_log(f"Timeout occurred after 900 seconds")
            messagebox.showerror("Timeout Error", timeout_msg)
            
        except FileNotFoundError as e:
            self.progress_var.set(0)
            self.status_label.config(text="ocrmypdf not found!")
            error_msg = "ocrmypdf is not installed or not in PATH.\n\nPlease install it using:\npip install ocrmypdf"
            self.log_message("✗ " + error_msg)
            self.debug_log(f"FileNotFoundError: {e}")
            messagebox.showerror("Error", error_msg)
            
        except PermissionError as e:
            self.progress_var.set(0)
            self.status_label.config(text="Permission error!")
            error_msg = f"Permission denied: {str(e)}\n\nTry running as Administrator or check file permissions."
            self.log_message("✗ " + error_msg)
            self.debug_log(f"PermissionError: {e}")
            messagebox.showerror("Permission Error", error_msg)
            
        except OSError as e:
            self.progress_var.set(0)
            self.status_label.config(text="System error!")
            error_msg = f"System error occurred: {str(e)}\n\nThis might be a system-level issue."
            self.log_message("✗ " + error_msg)
            self.debug_log(f"OSError: {e}")
            self.debug_log(f"OS Error details: errno={e.errno}, strerror={e.strerror}")
            messagebox.showerror("System Error", error_msg)
            
        except Exception as e:
            self.progress_var.set(0)
            self.status_label.config(text="An unexpected error occurred!")
            error_msg = f"An unexpected error occurred: {str(e)}"
            self.log_message("✗ " + error_msg)
            
            # Log full traceback in debug mode
            if self.debug_mode.get():
                tb = traceback.format_exc()
                self.debug_log(f"Full traceback: {tb}")
                
            messagebox.showerror("Unexpected Error", error_msg)
            
        finally:
            # Re-enable button
            self.process_button.config(state="normal")
            total_time = time.time() - start_time
            self.debug_log(f"Total process time: {total_time:.2f} seconds")
    
    def check_ghostscript_version(self):
        """Check if Ghostscript version has known issues"""
        try:
            gs_version = self.debug_info.get("ghostscript_version", "")
            if not gs_version:
                return False
                
            # Extract version number
            version_parts = gs_version.split('.')
            if len(version_parts) >= 2:
                major = int(version_parts[0])
                minor = int(version_parts[1])
                
                # Ghostscript 10.0.0 through 10.02.0 have known issues
                if major == 10 and minor <= 2:
                    self.debug_log(f"Detected problematic Ghostscript version: {gs_version}")
                    return True
                    
            return False
            
        except Exception as e:
            self.debug_log(f"Error checking Ghostscript version: {e}")
            return False
    
    def validate_ocr_command(self, cmd):
        """Validate OCR command before execution"""
        try:
            # Check if ocrmypdf is available
            result = subprocess.run(["ocrmypdf", "--help"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False, "ocrmypdf is not properly installed or not in PATH"
            
            # Check input file
            input_file = cmd[-2]  # Second to last argument
            if not os.path.exists(input_file):
                return False, f"Input file does not exist: {input_file}"
            
            # Check output directory
            output_file = cmd[-1]  # Last argument
            output_dir = os.path.dirname(output_file)
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except Exception as e:
                    return False, f"Cannot create output directory: {e}"
            
            # Check if output file is writable
            try:
                with open(output_file, 'a'):
                    pass
                os.remove(output_file)  # Clean up test file
            except Exception as e:
                return False, f"Output file is not writable: {e}"
            
            return True, "Command validation successful"
            
        except Exception as e:
            return False, f"Command validation error: {e}"
    
    def get_free_space(self, path):
        """Get free disk space for debugging"""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(str(path)), 
                                                         ctypes.pointer(free_bytes), None, None)
                return free_bytes.value
            else:  # Unix/Linux/macOS
                statvfs = os.statvfs(path)
                return statvfs.f_frsize * statvfs.f_bavail
        except Exception:
            return -1  # Unknown

    def get_pdf_page_count(self, path):
        """Return the number of pages in a PDF"""
        try:
            reader = PdfReader(path)
            return len(reader.pages)
        except Exception as e:
            self.debug_log(f"Error reading page count: {e}")
            return 0

    def process_large_pdf(self, input_file, output_file, base_cmd, num_pages):
        """Process large PDFs in smaller chunks to avoid errors"""
        try:
            self.log_message("Large PDF detected - processing in chunks")
            writer = PdfWriter()
            for start in range(1, num_pages + 1, self.chunk_size):
                end = min(start + self.chunk_size - 1, num_pages)
                tmp_output = str(Path(output_file).parent / f"tmp_{start}_{end}.pdf")
                cmd = base_cmd + ["--pages", f"{start}-{end}", input_file, tmp_output]
                self.debug_log(f"Running chunk {start}-{end}: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd(), timeout=900)
                if result.returncode != 0:
                    raise RuntimeError(result.stderr or f"Chunk {start}-{end} failed")
                writer.append(PdfReader(tmp_output))
                os.remove(tmp_output)
                progress = (end / num_pages) * 100
                self.progress_var.set(progress)
            with open(output_file, 'wb') as f:
                writer.write(f)
            self.progress_var.set(100)
        except Exception as e:
            raise RuntimeError(f"Large PDF processing error: {e}")
    
    def open_output_folder(self, file_path):
        try:
            folder_path = os.path.dirname(file_path)
            self.debug_log(f"Opening folder: {folder_path}")
            
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS and Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
                    
            self.debug_log("Folder opened successfully")
            
        except Exception as e:
            error_msg = f"Could not open folder: {str(e)}"
            self.log_message(error_msg)
            self.debug_log(f"Error opening folder: {e}")

def main():
    """Main function with enhanced error handling and logging"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            error_msg = f"This application requires Python 3.7 or higher.\nCurrent version: {sys.version}"
            print(error_msg)
            try:
                messagebox.showerror("Python Version Error", error_msg)
            except:
                print("Could not display error dialog")
            return

        # Create root window with error handling
        try:
            root = tk.Tk()
        except Exception as e:
            error_msg = f"Failed to initialize Tkinter: {e}"
            print(error_msg)
            return

        # Set up error handling for tkinter
        def handle_tk_error(exc, val, tb):
            error_msg = f"Tkinter Error: {val}"
            print(error_msg)
            if hasattr(root, 'app') and hasattr(root.app, 'debug_log'):
                root.app.debug_log(f"Tkinter error: {val}\nTraceback: {traceback.format_exc()}")
            try:
                messagebox.showerror("Application Error", error_msg)
            except:
                print("Could not display error dialog")

        root.report_callback_exception = handle_tk_error

        # Create application with error handling
        try:
            app = PDFOCRApp(root)
            root.app = app  # Store reference for error handling
        except Exception as e:
            error_msg = f"Failed to initialize application: {e}"
            print(error_msg)
            print(f"Traceback: {traceback.format_exc()}")
            try:
                messagebox.showerror("Initialization Error", error_msg)
            except:
                print("Could not display error dialog")
            return

        # Log startup
        try:
            app.logger.info("Application GUI initialized successfully")
            app.debug_log("Application startup completed")
        except Exception as e:
            print(f"Failed to log startup: {e}")

        # Start main loop
        try:
            root.mainloop()
        except Exception as e:
            error_msg = f"Main loop error: {e}"
            print(error_msg)
            print(f"Traceback: {traceback.format_exc()}")
            try:
                messagebox.showerror("Runtime Error", error_msg)
            except:
                print("Could not display error dialog")

    except ImportError as e:
        error_msg = f"Import Error: {e}\n\nPlease ensure all required packages are installed."
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        try:
            messagebox.showerror("Import Error", error_msg)
        except:
            print("Could not display error dialog")

    except Exception as e:
        error_msg = f"Critical Error: {e}\n\nThe application failed to start."
        print(error_msg)
        print(f"Full traceback: {traceback.format_exc()}")
        try:
            messagebox.showerror("Critical Error", error_msg)
        except:
            print("Could not display error dialog")

if __name__ == "__main__":
    main()