# library(Signac)
# library(Seurat)
# library(GenomicRanges)
# library(readr)
# library(dplyr)
# library(data.table)
# library(SingleCellExperiment)
# library(zellkonverter)
# Load required packages
packages <- c("Signac", "Seurat", "GenomicRanges", "readr", "dplyr", "data.table", "SingleCellExperiment", "zellkonverter", "optparse")

# Load all packages while suppressing messages and warnings
invisible(lapply(packages, function(pkg) {
  suppressMessages(suppressWarnings(library(pkg, character.only = TRUE)))
}))

# Parse command line arguments
option_list <- list(
  make_option(c("-p", "--peak"), type="character", help="Path to peak file"),
  make_option(c("-f", "--fragment"), type="character", help="Path to fragment file"),
  make_option(c("-m", "--metadata"), type="character", default=NULL, help="Path to metadata file (optional)"),
  make_option(c("-o", "--output"), type="character", help="Output h5ad file path"),
  make_option(c("-c", "--cell_col"), type="character", default="barcode", 
              help="Column name in metadata containing cell identifiers [default: %default]")
)

opt <- parse_args(OptionParser(option_list=option_list))

# Check if required arguments are provided
if (is.null(opt$peak) || is.null(opt$fragment) || is.null(opt$output)) {
  stop("Required arguments are missing: --peak, --fragment, --output")
}

# Initialize cells variable
cells <- NULL

# Read metadata if provided
if (!is.null(opt$metadata)) {
  meta_df <- fread(opt$metadata, header=TRUE)
  
  # Check if the specified cell column exists in metadata
  if (!opt$cell_col %in% colnames(meta_df)) {
    stop(sprintf("Column '%s' not found in metadata file. Available columns: %s", 
                 opt$cell_col, paste(colnames(meta_df), collapse=", ")))
  }
  
  # Get cell identifiers from the specified column
  cells <- unique(meta_df[[opt$cell_col]])
  print(cells[1:5])
  cat(sprintf("Found %d unique cells in metadata column '%s'\n", length(cells), opt$cell_col))
} else {
  cat("No metadata provided. Will process all cells from fragment file.\n")
}

features <- read.table(opt$peak, header=FALSE)
colnames(features) <- c("chr", "start", "end")
features <- makeGRangesFromDataFrame(features)

# Create fragment object
fragments <- CreateFragmentObject(opt$fragment)

# Check if peak matrix file exists
peak_matrix_file <- paste0(tools::file_path_sans_ext(opt$output), "_peak_matrix.rds")

if (file.exists(peak_matrix_file)) {
  cat("Loading existing peak matrix from:", peak_matrix_file, "\n")
  peak_matrix <- readRDS(peak_matrix_file)
  cat("Loaded peak matrix with dimensions:", dim(peak_matrix), "\n")
} else {
  cat("Generating new peak matrix...\n")
  # Print debug information
  cat("Number of features:", length(features), "\n")
  cat("Number of cells:", length(cells), "\n")
  cat("First few feature ranges:\n")
  print(head(features))
  cat("First few cell barcodes:\n")
  print(head(cells))

  # Generate peak matrix
  peak_matrix <- FeatureMatrix(
    fragments = fragments,
    features = features,
    cells = cells,
    process_n = 2000,
    sep = c(":", "-"),
    verbose = TRUE
  )

  # Print dimensions for debugging
  cat("Peak matrix dimensions:", dim(peak_matrix), "\n")
  cat("Number of features:", length(features), "\n")

  # Create row names for the peak matrix
  row_names <- paste0(seqnames(features), ":", start(features), "-", end(features))
  rownames(peak_matrix) <- row_names

  # Save intermediate peak matrix
  saveRDS(peak_matrix, peak_matrix_file)
  cat("Saved intermediate peak matrix to:", peak_matrix_file, "\n")
}

# Verify dimensions match
# if(ncol(peak_matrix) != length(cells)) {
#   stop("Number of cells in peak matrix (", ncol(peak_matrix), 
#        ") does not match number of cells in metadata (", length(cells), ")")
# }

# Create DataFrame with explicit string conversion
# col_data <- DataFrame(lapply(meta_df, as.character), 
                    #  row.names = meta_df[[opt$cell_col]])

# Create SingleCellExperiment object
sce <- SingleCellExperiment(
  assays = list(counts = peak_matrix),
  # colData = cells
)

# Verify the object was created correctly
cat("SingleCellExperiment dimensions:", dim(sce), "\n")

# Save as h5ad file
writeH5AD(sce, opt$output)
cat("Saved:", opt$output, "\n")