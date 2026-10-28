# =============================================================================
# Enhanced Cluster Analysis Visualization
# Creates horizontal boxplots for R2 timing metrics by cluster groups
# =============================================================================

# Load required libraries
suppressPackageStartupMessages({
  library(ggplot2)
  library(readxl)
  library(dplyr)
})

# =============================================================================
# Data Loading and Preparation
# =============================================================================

# Load data
file_path <- "output-cluster-with-score.xlsx"
df <- read_excel(file_path)

# Define cluster group mapping function
map_cluster_to_group <- function(cluster) {
  case_when(
    cluster == 1 ~ 'Extended Engager',
    cluster == 2 ~ 'Brief Participants', 
    TRUE ~ NA_character_
  )
}

# Prepare individual datasets with consistent structure
prepare_metric_data <- function(data, metric_col, panel_name) {
  data %>%
    select(all_of(metric_col), Cluster) %>%
    mutate(
      Group = map_cluster_to_group(Cluster),
      Panel = panel_name,
      Value = .data[[metric_col]]
    ) %>%
    select(Value, Group, Panel) %>%
    filter(!is.na(Group))
}

# Create datasets for each metric
r2_time_to_start <- prepare_metric_data(df, "R2.Time.To.Start", "Time to Start")
r2_time_to_end <- prepare_metric_data(df, "R2.Time.To.End", "Time to End") 
r2_duration <- prepare_metric_data(df, "R2.Dur", "Duration")

# Combine all datasets
combined_data <- bind_rows(
  r2_time_to_start,
  r2_time_to_end, 
  r2_duration
)

# Set factor levels for consistent ordering
combined_data$Group <- factor(combined_data$Group, 
                              levels = c("Extended Engager", "Brief Participants"))

combined_data$Panel <- factor(combined_data$Panel,
                              levels = c("Time to Start", "Time to End", "Duration"))

# =============================================================================
# Visualization
# =============================================================================

# Define color palette
group_colors <- c(
  "Extended Engager" = "#2E86C1",        # Professional blue
  "Brief Participants" = "#28B463"
)

# Create the main plot
main_plot <- ggplot(combined_data, aes(x = Value, y = Group, fill = Group)) +
  
  # Add boxplots with enhanced styling
  geom_boxplot(
    outlier.shape = 21,
    outlier.fill = "white",
    outlier.stroke = 0.5,
    alpha = 0.8,
    size = 0.6
  ) +
  
  # Customize scales and labels
  scale_fill_manual(
    name = "Cluster Groups",
    values = group_colors
  ) +
  
  labs(
    x = "Time (Minutes)",
    y = NULL
  ) +
  
  # Apply clean theme
  theme_minimal(base_size = 11) +
  
  # Customize theme elements
  theme(
    # Legend styling
    legend.position = "top",
    legend.title = element_text(size = 12, face = "bold"),
    legend.text = element_text(size = 10),
    legend.key.size = unit(0.8, "cm"),
    
    # Title styling
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5, margin = margin(b = 5)),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "gray40", margin = margin(b = 15)),
    
    # Axis styling
    axis.title.x = element_text(size = 11, face = "bold", margin = margin(t = 10)),
    axis.text.x = element_text(size = 10),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    
    # Panel styling
    panel.border = element_rect(color = "gray30", fill = NA, size = 0.8),
    panel.grid.major.x = element_line(color = "gray90", size = 0.3),
    panel.grid.minor.x = element_blank(),
    panel.grid.major.y = element_blank(),
    
    # Facet styling
    strip.background = element_rect(fill = "gray95", color = "gray70", size = 0.5),
    strip.text = element_text(size = 11, face = "bold", color = "gray20"),
    
    # Overall plot margins
    plot.margin = margin(15, 20, 15, 15)
  ) +
  
  # Create faceted panels
  facet_wrap(~ Panel, ncol = 1, scales = "free_x")

# Display the plot
print(main_plot)

# =============================================================================
# Optional: Save high-quality plot
# =============================================================================

# Uncomment the following lines to save the plot
# ggsave(
#   filename = "r2_cluster_analysis.png",
#   plot = main_plot,
#   width = 10, 
#   height = 8, 
#   dpi = 300,
#   bg = "white"
# )

# =============================================================================
# Summary Statistics (Optional)
# =============================================================================

# Generate summary statistics by group and panel
summary_stats <- combined_data %>%
  group_by(Panel, Group) %>%
  summarise(
    n = n(),
    mean = round(mean(Value, na.rm = TRUE), 2),
    median = round(median(Value, na.rm = TRUE), 2),
    sd = round(sd(Value, na.rm = TRUE), 2),
    min = round(min(Value, na.rm = TRUE), 2),
    max = round(max(Value, na.rm = TRUE), 2),
    .groups = "drop"
  )

# Display summary statistics
print("Summary Statistics by Group and Metric:")
print(summary_stats)

