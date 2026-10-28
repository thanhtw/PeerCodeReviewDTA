# ============================================================================
# Clustered Data Visualization: Horizontal Boxplots by Group
# ============================================================================

# Load required libraries
suppressPackageStartupMessages({
  library(ggplot2)
  library(readxl)
  library(dplyr)
})

# ============================================================================
# 1. DATA LOADING AND PREPARATION
# ============================================================================

# Load the clustered data
file_path <- "output-cluster-with-score.xlsx"
df <- read_excel(file_path)

# Define cluster labels
cluster_labels <- c(
  "1" = "Extended Engagers",
  "2" = "Brief Participants"
)

# Define panel information with proper labels
panel_info <- list(
  list(column = "R1.C1.Sub", panel = "R1.C1.Sub", label = "Total R1 Func Count"),
  list(column = "R1.C2.Sub", panel = "R1.C2.Sub", label = "Total R1 Read Count"),
  list(column = "R1.C3.Sub", panel = "R1.C3.Sub", label = "Total R1 Comp Count"),
  list(column = "R1.MF", panel = "R1.MF.Sub", label = "Total R1 MF Count")
)

# ============================================================================
# 2. DATA TRANSFORMATION
# ============================================================================

# Function to prepare panel data
prepare_panel_data <- function(df, column, panel_name, panel_label) {
  data.frame(
    Value = df[[column]],
    Cluster = df$Cluster,
    Group = factor(cluster_labels[as.character(df$Cluster)], 
                   levels = c("Extended Engagers", "Brief Participants")),
    Panel = panel_name,
    Panel_Label = panel_label,
    stringsAsFactors = FALSE
  )
}

# Create combined dataset
combined_data <- do.call(rbind, lapply(panel_info, function(info) {
  prepare_panel_data(df, info$column, info$panel, info$label)
}))

# Ensure proper factor ordering for panels
combined_data$Panel <- factor(combined_data$Panel, 
                              levels = c("R1.C1.Sub", "R1.C2.Sub", "R1.C3.Sub", "R1.MF.Sub"))

# ============================================================================
# 3. VISUALIZATION SETTINGS
# ============================================================================

# Define color palette
colors <- c(
  "Extended Engagers" = "#2E86C1",        # Professional blue
  "Brief Participants" = "#28B463"   # Professional magenta
)

# Create panel labels for facets
panel_labels <- setNames(
  c("Functionality Submissions Count", "Readability Submissions Count", "Documentation Submissions Count", "Meaningful Feedback Submissions Count"),
  c("R1.C1.Sub", "R1.C2.Sub", "R1.C3.Sub", "R1.MF.Sub")
)

# ============================================================================
# 4. CREATE ENHANCED BOXPLOT
# ============================================================================

enhanced_plot <- ggplot(combined_data, aes(x = Value, y = Group, fill = Group)) +
  
  # Main boxplot with improved aesthetics
  geom_boxplot(
    alpha = 0.8,
    outlier.shape = 21,
    outlier.size = 2,
    outlier.fill = "white",
    outlier.stroke = 1,
    width = 0.6
  ) +
  
  # Add subtle jitter points for data distribution
  geom_point(
    aes(color = Group),
    position = position_jitter(height = 0.15, width = 0),
    alpha = 0.4,
    size = 1.2
  ) +
  
  # Customize scales
  scale_fill_manual(values = colors, name = "Student Groups") +
  scale_color_manual(values = colors, guide = "none") +
  scale_x_continuous(
    expand = expansion(mult = c(0.02, 0.05)),
    breaks = scales::pretty_breaks(n = 5)
  ) +
  
  # Labels and title
  labs(
    x = "Number of Submissions",
    y = NULL
  ) +
  
  # Faceting
  facet_wrap(
    ~ Panel, 
    ncol = 1, 
    scales = "free_x",
    labeller = labeller(Panel = panel_labels),
    strip.position = "top"
  ) +
  
  # Theme customization
  theme_minimal(base_size = 11) +
  theme(
    # Legend
    legend.position = "top",
    legend.title = element_text(face = "bold", size = 10),
    legend.text = element_text(size = 9),
    legend.margin = margin(b = 15),
    
    # Axes
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    axis.text.x = element_text(size = 9),
    axis.title.x = element_text(face = "bold", size = 10, margin = margin(t = 10)),
    
    # Facet strips
    strip.text = element_text(
      face = "bold", 
      size = 10, 
      margin = margin(b = 8, t = 8)
    ),
    strip.background = element_rect(
      fill = "grey92", 
      color = "grey70", 
      size = 0.5
    ),
    
    # Panels
    panel.border = element_rect(
      colour = "grey70", 
      fill = NA, 
      size = 0.5
    ),
    panel.spacing = unit(0.8, "lines"),
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_line(color = "grey90", size = 0.3),
    
    # Plot area
    plot.title = element_text(
      face = "bold", 
      size = 12, 
      hjust = 0.5,
      margin = margin(b = 5)
    ),
    plot.subtitle = element_text(
      size = 10, 
      hjust = 0.5, 
      color = "grey40",
      margin = margin(b = 15)
    ),
    plot.caption = element_text(
      size = 8, 
      color = "grey50", 
      hjust = 1,
      margin = margin(t = 10)
    ),
    plot.margin = margin(15, 15, 15, 15)
  )

# Display the plot
print(enhanced_plot)

# ============================================================================
# 5. OPTIONAL: SAVE HIGH-QUALITY PLOT
# ============================================================================

# Save as high-quality PNG
ggsave(
  "enhanced_boxplot_clusters.png",
  plot = enhanced_plot,
  width = 10,
  height = 8,
  dpi = 300,
  bg = "white"
)

# Save as PDF for publications
ggsave(
  "enhanced_boxplot_clusters.pdf",
  plot = enhanced_plot,
  width = 10,
  height = 8,
  device = "pdf"
)

# ============================================================================
# 6. SUMMARY STATISTICS (OPTIONAL)
# ============================================================================

# Generate summary statistics by group and panel
summary_stats <- combined_data %>%
  group_by(Panel, Group) %>%
  summarise(
    n = n(),
    mean = round(mean(Value, na.rm = TRUE), 2),
    median = round(median(Value, na.rm = TRUE), 2),
    sd = round(sd(Value, na.rm = TRUE), 2),
    min = min(Value, na.rm = TRUE),
    max = max(Value, na.rm = TRUE),
    .groups = 'drop'
  )

# Display summary
print("Summary Statistics by Group and Activity Type:")
print(summary_stats)

