# ===============================================================================
# K-MEANS CLUSTERING ANALYSIS WITH ENHANCED VISUALIZATION
# ===============================================================================
# This script performs comprehensive clustering analysis with:
# 1. Data preprocessing and PCA dimensionality reduction
# 2. Multiple methods for determining optimal number of clusters
# 3. Enhanced K-means clustering with multiple visualizations
# 4. Comprehensive results analysis and export
# ===============================================================================

# Load Required Libraries
# ===============================================================================
required_packages <- c("readxl", "rgl", "openxlsx", "factoextra", 
                       "cluster", "NbClust", "ggplot2", "plotly", 
                       "corrplot", "RColorBrewer", "gridExtra")

install_if_missing <- function(packages) {
  missing_packages <- packages[!(packages %in% installed.packages()[,"Package"])]
  if(length(missing_packages)) {
    cat("Installing missing packages:", paste(missing_packages, collapse = ", "), "\n")
    install.packages(missing_packages)
  }
}

install_if_missing(required_packages)

# Load libraries with error handling
library(readxl)
library(rgl)
library(openxlsx)
library(factoextra)
library(cluster)
library(NbClust)
library(ggplot2)
library(plotly)
library(corrplot)
library(RColorBrewer)
library(gridExtra)

# Configuration Parameters
# ===============================================================================
CONFIG <- list(
  INPUT_FILE = "Merge-Data.xlsx",
  OUTPUT_PREFIX = "clustering_results",
  RANDOM_SEED = 42,
  MAX_CLUSTERS = 10,
  MIN_CLUSTERS = 2,
  PCA_COMPONENTS = 3,
  FEATURE_COLUMNS = c(
    'Effort_R1','Effort_R1','R1.Dur','R2.Dur',
    'R1.Start', 'R1.End',
    'R2.Start', 'R2.End',
    'MF_Ratio_R1', 'MF_Ratio_R2'
  )
)

set.seed(CONFIG$RANDOM_SEED)

# Utility Functions
# ===============================================================================
print_section <- function(title, char = "=") {
  cat("\n", paste(rep(char, 60), collapse = ""), "\n")
  cat(toupper(title), "\n")
  cat(paste(rep(char, 60), collapse = ""), "\n")
}

print_subsection <- function(title) {
  cat("\n", paste(rep("-", 40), collapse = ""), "\n")
  cat(title, "\n")
  cat(paste(rep("-", 40), collapse = ""), "\n")
}

# Data Loading and Preprocessing
# ===============================================================================
print_section("DATA LOADING AND PREPROCESSING")

# Load and validate data
if (!file.exists(CONFIG$INPUT_FILE)) {
  stop(paste("Input file", CONFIG$INPUT_FILE, "not found!"))
}

df <- read_excel(CONFIG$INPUT_FILE)
cat("✓ Dataset loaded successfully!\n")
cat("  Dimensions:", nrow(df), "rows ×", ncol(df), "columns\n")

# Validate feature columns
missing_cols <- CONFIG$FEATURE_COLUMNS[!(CONFIG$FEATURE_COLUMNS %in% colnames(df))]
if (length(missing_cols) > 0) {
  stop(paste("Missing columns:", paste(missing_cols, collapse = ", ")))
}

# Extract features
X <- df[, CONFIG$FEATURE_COLUMNS]
cat("✓ Selected", length(CONFIG$FEATURE_COLUMNS), "features for clustering\n")

# Data quality check
na_count <- sum(is.na(X))
if (na_count > 0) {
  cat("⚠ Warning:", na_count, "missing values detected\n")
  X <- na.omit(X)  # Remove rows with missing values
  cat("✓ Removed rows with missing values. New dimensions:", nrow(X), "×", ncol(X), "\n")
}

# Feature scaling
X_scaled <- scale(X)
cat("✓ Features standardized (mean=0, sd=1)\n")

# Principal Component Analysis
# ===============================================================================
print_section("PRINCIPAL COMPONENT ANALYSIS")

pca <- prcomp(X_scaled, center = TRUE, scale. = TRUE)
pca_summary <- summary(pca)

# Display PCA results
cat("PCA Results:\n")
cat("  PC1 explains", round(pca_summary$importance[2, 1] * 100, 1), "% of variance\n")
cat("  PC2 explains", round(pca_summary$importance[2, 2] * 100, 1), "% of variance\n")
cat("  PC3 explains", round(pca_summary$importance[2, 3] * 100, 1), "% of variance\n")
cat("  First 3 PCs explain", round(pca_summary$importance[3, 3] * 100, 1), "% of total variance\n")

# Extract PCA components
X_pca <- pca$x[, 1:CONFIG$PCA_COMPONENTS]
pca_df <- data.frame(
  PC1 = X_pca[, 1], 
  PC2 = X_pca[, 2], 
  PC3 = X_pca[, 3]
)

# Visualize PCA variance explanation
pca_var_plot <- fviz_eig(pca, addlabels = TRUE, ylim = c(0, 50)) +
  ggtitle("PCA: Variance Explained by Each Component") +
  theme_minimal()
print(pca_var_plot)

# Optimal Cluster Number Determination
# ===============================================================================
print_section("OPTIMAL CLUSTER NUMBER DETERMINATION")

# Initialize results storage
cluster_metrics <- data.frame(
  k = CONFIG$MIN_CLUSTERS:CONFIG$MAX_CLUSTERS,
  wss = NA,
  silhouette = NA,
  gap = NA
)

# Method 1: Elbow Method (Within-Cluster Sum of Squares)
# -------------------------------------------------------------------------------
print_subsection("1. ELBOW METHOD")

calculate_wss <- function(k) {
  if (k == 1) {
    return(sum(apply(X_pca, 2, function(x) sum((x - mean(x))^2))))
  }
  kmeans(X_pca, centers = k, nstart = 25, iter.max = 300)$tot.withinss
}

wss_values <- sapply(1:CONFIG$MAX_CLUSTERS, calculate_wss)
cluster_metrics$wss[cluster_metrics$k >= 1] <- wss_values[CONFIG$MIN_CLUSTERS:CONFIG$MAX_CLUSTERS]

# Create enhanced elbow plot
elbow_data <- data.frame(k = 1:CONFIG$MAX_CLUSTERS, wss = wss_values)
elbow_plot <- ggplot(elbow_data, aes(x = k, y = wss)) +
  geom_line(color = "steelblue", size = 1.2) +
  geom_point(color = "darkblue", size = 3) +
  geom_point(data = subset(elbow_data, k == 4), color = "red", size = 4) +
  labs(x = "Number of Clusters (k)",
       y = "Total Within-Cluster Sum of Squares") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, size = 14, face = "bold")) +
  scale_x_continuous(breaks = 1:CONFIG$MAX_CLUSTERS)

print(elbow_plot)

# Method 2: Silhouette Analysis
# -------------------------------------------------------------------------------
print_subsection("2. SILHOUETTE METHOD")

calculate_silhouette <- function(k) {
  if (k < 2) return(NA)
  kmeans_result <- kmeans(X_pca, centers = k, nstart = 25, iter.max = 300)
  sil_result <- silhouette(kmeans_result$cluster, dist(X_pca))
  mean(sil_result[, 3])
}

silhouette_scores <- sapply(CONFIG$MIN_CLUSTERS:CONFIG$MAX_CLUSTERS, calculate_silhouette)
cluster_metrics$silhouette <- silhouette_scores

optimal_k_silhouette <- which.max(silhouette_scores) + 1
cat("✓ Optimal k (Silhouette method):", optimal_k_silhouette, "\n")

# Enhanced silhouette plot
sil_data <- data.frame(k = CONFIG$MIN_CLUSTERS:CONFIG$MAX_CLUSTERS, silhouette = silhouette_scores)
sil_plot <- ggplot(sil_data, aes(x = k, y = silhouette)) +
  geom_line(color = "darkgreen", size = 1.2) +
  geom_point(color = "forestgreen", size = 3) +
  geom_point(data = subset(sil_data, k == optimal_k_silhouette), color = "red", size = 4) +
  labs(x = "Number of Clusters (k)",
       y = "Average Silhouette Width") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, size = 14, face = "bold")) +
  scale_x_continuous(breaks = CONFIG$MIN_CLUSTERS:CONFIG$MAX_CLUSTERS)

print(sil_plot)

# Method 3: Gap Statistic
# -------------------------------------------------------------------------------
print_subsection("3. GAP STATISTIC METHOD")

tryCatch({
  gap_stat <- clusGap(X_pca, FUN = kmeans, nstart = 25, 
                      K.max = CONFIG$MAX_CLUSTERS, B = 50, verbose = FALSE)
  optimal_k_gap <- maxSE(gap_stat$Tab[, "gap"], gap_stat$Tab[, "SE.sim"])
  
  gap_plot <- fviz_gap_stat(gap_stat) +
    theme_minimal() +
    theme(plot.title = element_text(hjust = 0.5, size = 14, face = "bold"))
  
  print(gap_plot)
  cat("✓ Optimal k (Gap Statistic):", optimal_k_gap, "\n")
  
}, error = function(e) {
  cat("⚠ Gap statistic calculation failed:", e$message, "\n")
  optimal_k_gap <- optimal_k_silhouette
})

# Method 4: Multiple Indices (NbClust)
# -------------------------------------------------------------------------------
print_subsection("4. MULTIPLE INDICES ANALYSIS")

tryCatch({
  nb_result <- NbClust(data = X_pca, diss = NULL, distance = "euclidean",
                       min.nc = CONFIG$MIN_CLUSTERS, max.nc = CONFIG$MAX_CLUSTERS, 
                       method = "kmeans", index = "all")
  
  nb_table <- table(nb_result$Best.nc[1,])
  cat("NbClust recommendations:\n")
  print(nb_table)
  
  optimal_k_nb <- as.numeric(names(nb_table)[which.max(nb_table)])
  cat("✓ Most recommended k (NbClust):", optimal_k_nb, "\n")
  
}, error = function(e) {
  cat("⚠ NbClust analysis failed:", e$message, "\n")
  optimal_k_nb <- optimal_k_silhouette
})

# Final Cluster Number Decision
# -------------------------------------------------------------------------------
print_subsection("CLUSTER NUMBER RECOMMENDATION SUMMARY")

# Determine final optimal k (you can modify this logic)
optimal_k_final <- optimal_k_silhouette  # Using silhouette as primary criterion

cat("📊 SUMMARY OF RECOMMENDATIONS:\n")
cat("  • Silhouette method suggests:", optimal_k_silhouette, "clusters\n")
if (exists("optimal_k_gap")) cat("  • Gap statistic suggests:", optimal_k_gap, "clusters\n")
if (exists("optimal_k_nb")) cat("  • NbClust majority vote:", optimal_k_nb, "clusters\n")
cat("  • Final choice:", optimal_k_final, "clusters\n")

# K-Means Clustering with Enhanced Visualization
# ===============================================================================
print_section("K-MEANS CLUSTERING AND VISUALIZATION")

# Perform final clustering
kmeans_result <- kmeans(X_pca, centers = optimal_k_final, nstart = 25, iter.max = 300)
df$Cluster <- as.factor(kmeans_result$cluster)
pca_df$Cluster <- as.factor(kmeans_result$cluster)

cat("✓ K-means clustering completed with", optimal_k_final, "clusters\n")
cat("  Cluster sizes:", paste(table(df$Cluster), collapse = ", "), "\n")

# Create color palette
cluster_colors <- brewer.pal(min(optimal_k_final, 11), "Spectral")
if (optimal_k_final > 11) {
  cluster_colors <- rainbow(optimal_k_final)
}

# Visualization 1: 2D PCA Plot
# -------------------------------------------------------------------------------
print_subsection("2D VISUALIZATION")

pca_2d_plot <- ggplot(pca_df, aes(x = PC1, y = PC2, color = Cluster)) +
  geom_point(size = 3, alpha = 0.7) +
  stat_ellipse(type = "confidence", level = 0.95, size = 1) +
  scale_color_manual(values = cluster_colors) +
  labs(title = paste("K-Means Clustering Results (k =", optimal_k_final, ")"),
       subtitle = "2D PCA Visualization with 95% Confidence Ellipses",
       x = paste("PC1 (", round(pca_summary$importance[2, 1] * 100, 1), "% variance)", sep = ""),
       y = paste("PC2 (", round(pca_summary$importance[2, 2] * 100, 1), "% variance)", sep = "")) +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
        plot.subtitle = element_text(hjust = 0.5, size = 12),
        legend.position = "right")

print(pca_2d_plot)

# Visualization 2: Interactive 3D Plot
# -------------------------------------------------------------------------------
print_subsection("3D INTERACTIVE VISUALIZATION")

# Create interactive 3D plot using plotly
plot_3d_interactive <- plot_ly(pca_df, x = ~PC1, y = ~PC2, z = ~PC3, 
                               color = ~Cluster, colors = cluster_colors,
                               type = 'scatter3d', mode = 'markers',
                               marker = list(size = 5, opacity = 0.8)) %>%
  layout(title = list(text = paste(""),
                      font = list(size = 16)),
         scene = list(
           xaxis = list(title = paste("PC1")),
           yaxis = list(title = paste("PC2")),
           zaxis = list(title = paste("PC3"))
         ))

print(plot_3d_interactive)

# Visualization 3: Static 3D Plot using rgl
# -------------------------------------------------------------------------------
print_subsection("3D STATIC VISUALIZATION")

# Create 3D scatter plot
open3d(windowRect = c(100, 100, 800, 800))
point_colors <- cluster_colors[as.numeric(df$Cluster)]

plot3d(pca_df$PC1, pca_df$PC2, pca_df$PC3,
       col = point_colors, type = "s", size = 2,
       xlab = paste("PC1"),
       ylab = paste("PC2"),
       zlab = paste("PC3"),
       main = paste(""))

# Add grid and styling
grid3d(c("x", "y", "z"))
rgl.bbox(color = c("#333377", "black"), emission = "#333377", 
         specular = "#3333FF", shininess = 5, alpha = 0.8)

# Add cluster centers and labels
cluster_centers <- aggregate(pca_df[, 1:3], by = list(pca_df$Cluster), FUN = mean)
for (i in 1:nrow(cluster_centers)) {
  # Add cluster center points
  plot3d(cluster_centers$PC1[i], cluster_centers$PC2[i], cluster_centers$PC3[i],
         col = "black", type = "s", size = 4, add = TRUE)
  
  # Add cluster labels
  text3d(cluster_centers$PC1[i], cluster_centers$PC2[i], cluster_centers$PC3[i],
         texts = paste("C", i), col = "white", cex = 1.5, adj = c(0.5, -0.5))
}

# Add legend
legend3d("topright", legend = paste("Cluster", 1:optimal_k_final),
         pch = 16, col = cluster_colors, cex = 1.2, inset = c(0.02))

# Save 3D plot
snapshot_file <- paste0(CONFIG$OUTPUT_PREFIX, "_3d_plot_new1", optimal_k_final, ".png")
rgl.snapshot(snapshot_file, fmt = "png")
cat("✓ 3D plot saved as:", snapshot_file, "\n")


# Cluster Analysis and Interpretation
# ===============================================================================
print_section("CLUSTER ANALYSIS")

# Cluster statistics
print_subsection("CLUSTER STATISTICS")

cluster_stats <- data.frame(
  Cluster = 1:optimal_k_final,
  Size = as.numeric(table(df$Cluster)),
  Percentage = round(as.numeric(table(df$Cluster)) / nrow(df) * 100, 1)
)

cat("Cluster Distribution:\n")
print(cluster_stats)

# Within-cluster sum of squares for each cluster
cat("\nWithin-cluster sum of squares:\n")
print(kmeans_result$withinss)
cat("Total within-cluster sum of squares:", kmeans_result$tot.withinss, "\n")
cat("Between-cluster sum of squares:", kmeans_result$betweenss, "\n")
cat("Total sum of squares:", kmeans_result$totss, "\n")

# Silhouette analysis for final clustering
print_subsection("SILHOUETTE ANALYSIS")

sil_final <- silhouette(kmeans_result$cluster, dist(X_pca))
sil_plot_final <- fviz_silhouette(sil_final) +
  ggtitle(paste("Silhouette Analysis for k =", optimal_k_final)) +
  theme_minimal()

print(sil_plot_final)

cat("Average silhouette width:", round(mean(sil_final[, 3]), 3), "\n")

# Feature importance in clustering
print_subsection("FEATURE CONTRIBUTION ANALYSIS")

# Calculate feature contributions to PC1, PC2, PC3
feature_contrib <- data.frame(
  Feature = CONFIG$FEATURE_COLUMNS,
  PC1_Contrib = abs(pca$rotation[, 1]),
  PC2_Contrib = abs(pca$rotation[, 2]),
  PC3_Contrib = abs(pca$rotation[, 3])
)

# Sort by total contribution
feature_contrib$Total_Contrib <- feature_contrib$PC1_Contrib + 
  feature_contrib$PC2_Contrib + 
  feature_contrib$PC3_Contrib
feature_contrib <- feature_contrib[order(-feature_contrib$Total_Contrib), ]

cat("Top contributing features to clustering:\n")
print(head(feature_contrib, 8))

# Export Results
# ===============================================================================
print_section("EXPORTING RESULTS")

# Save clustered data
output_file <- paste0(CONFIG$OUTPUT_PREFIX, "_clustered_data_k", optimal_k_final, ".xlsx")
write.xlsx(df, output_file, rowNames = FALSE)
cat("✓ Clustered data saved to:", output_file, "\n")

# Save cluster summary
cluster_summary <- list(
  "Cluster_Statistics" = cluster_stats,
  "Feature_Contributions" = feature_contrib,
  "PCA_Summary" = pca_summary$importance,
  "Clustering_Metrics" = data.frame(
    Method = c("Silhouette", "Gap_Statistic", "NbClust"),
    Recommended_k = c(optimal_k_silhouette, 
                      ifelse(exists("optimal_k_gap"), optimal_k_gap, NA),
                      ifelse(exists("optimal_k_nb"), optimal_k_nb, NA))
  )
)

summary_file <- paste0(CONFIG$OUTPUT_PREFIX, "_summary_k", optimal_k_final, ".xlsx")
write.xlsx(cluster_summary, summary_file)
cat("✓ Cluster summary saved to:", summary_file, "\n")

# Final Summary
# ===============================================================================
print_section("ANALYSIS COMPLETE")

cat("🎉 CLUSTERING ANALYSIS SUMMARY:\n")
cat("  • Dataset:", nrow(df), "observations,", length(CONFIG$FEATURE_COLUMNS), "features\n")
cat("  • Optimal number of clusters:", optimal_k_final, "\n")
cat("  • PCA variance explained:", round(pca_summary$importance[3, 3] * 100, 1), "%\n")
cat("  • Average silhouette width:", round(mean(sil_final[, 3]), 3), "\n")
cat("  • Files generated:\n")
cat("    -", output_file, "\n")
cat("    -", summary_file, "\n")
cat("    -", snapshot_file, "\n")
cat("\n✓ All analyses completed successfully!\n")

# Close 3D window
rgl.close()