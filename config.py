# Configuration settings for the R Code Executor application

# Base directory for storing output files from R script executions
BASE_OUTPUT_DIR = 'output_files'

# Docker image name for the R executor environment
R_EXECUTOR_IMAGE = 'my-r-executor:latest'

# Resource limits for Docker containers
CPU_LIMIT = 1  # Number of CPU cores
MEMORY_LIMIT = '512m'  # Memory limit (e.g., '512m', '1g')
TIMEOUT = 10  # Execution timeout in seconds for R scripts

# List of forbidden patterns (regular expressions) in R code to prevent unsafe operations
FORBIDDEN_PATTERNS = [
    r'\bsystem\b',
    r'\bfile\b',
    r'\bunlink\b',
    r'\bsetwd\b',
    r'\bgetwd\b',
    r'\beval\b',
    r'\bparse\b',
    r'\blibrary\b',
    r'\brequire\b',
    r'\bsink\b',
    r'\binstall\.packages\b',
    r'\bread\.table\b',
    r'\bwrite\.table\b'
]

# Time-to-live (TTL) in seconds for output files and directories
# Directories older than this will be cleaned up periodically
FILE_TTL_SECONDS = 1800  # 30 minutes
