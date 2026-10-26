# Load required libraries
library(ggplot2)
library(scales)

# Create the data in the correct order: HW1-HW7, Midterm, Final
assignments <- c("HW1", "HW2", "HW3", "HW4", "HW5", "HW6", "HW7", "Midterm", "Final")
extended_engagers <- c(79.02, 79.02, 95.56, 91.02, 91.37, 85.95, 89.54, 69.34, 70.20)
brief_participants <- c(67.41, 67.41, 83.56, 68.03, 68.63, 65.84, 65.63, 58.28, 55.91)

# Create data frame with factor levels to maintain order
df <- data.frame(
  Assignment = rep(factor(assignments, levels = assignments), 2),
  Group = rep(c("Extended Engagers", "Brief Participants"), each = length(assignments)),
  Score = c(extended_engagers, brief_participants)
)

# Calculate standard errors or confidence intervals (example with hypothetical SEs)
# Replace with actual SE calculations from your data
df$SE <- c(
  rep(c(2.1, 2.3, 1.8, 2.0, 1.9, 2.2, 2.1, 2.5, 2.4), 2) # Example SEs
)

# Create the enhanced column chart
p <- ggplot(df, aes(x = Assignment, y = Score, fill = Group)) +
  geom_col(position = position_dodge(width = 0.8), 
           width = 0.7, 
           alpha = 0.8,
           color = "black", 
           size = 0.3) +
  
  # Add error bars
  geom_errorbar(aes(ymin = Score - SE, ymax = Score + SE),
                position = position_dodge(width = 0.8),
                width = 0.2,
                size = 0.4) +
  
  # Professional color scheme (colorblind-friendly)
  scale_fill_manual(values = c("Extended Engagers" = "#2E86C1", 
                               "Brief Participants" = "#28B463"),
                    name = "Student Group") +
  
  # Improved axis formatting
  scale_y_continuous(limits = c(0, 105),
                     breaks = seq(0, 100, 20),
                     expand = expansion(mult = c(0, 0.05))) +
  
  # Professional labels
  labs(
    x = "",
    y = "Mean Score (%)"
  ) +
  
  # Journal-quality theme
  theme_classic() +
  theme(
    # Text formatting
    axis.title = element_text(size = 12, face = "bold"),
    axis.text = element_text(size = 10, color = "black"),
    legend.title = element_text(size = 11, face = "bold"),
    legend.text = element_text(size = 10),
    
    # Layout
    legend.position = "bottom",
    legend.margin = margin(t = -10),
    panel.border = element_rect(color = "black", fill = NA, size = 0.5),
    
    # Remove unnecessary elements
    panel.grid = element_blank(),
    
    # Spacing
    plot.margin = margin(20, 20, 20, 20)
  ) +
  
  # Add significance indicators if you have statistical tests
  # annotate("text", x = 3, y = 98, label = "***", size = 4) +
  
  # Ensure consistent spacing
  scale_x_discrete(expand = expansion(mult = c(0.05, 0.05)))

# Display the plot
print(p)

# Optional: Save as high-resolution image for journal submission
ggsave("academic_performance_chart.png", plot = p, width = 10, height = 6, dpi = 300, units = "in")
ggsave("academic_performance_chart.pdf", plot = p, width = 10, height = 6, units = "in")
