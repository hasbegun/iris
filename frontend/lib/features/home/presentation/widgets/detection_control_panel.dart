import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';

/// Control panel for filtering and adjusting detection visualization
class DetectionControlPanel extends StatelessWidget {
  final List<Detection> detections;
  final double minConfidence;
  final Set<String> filteredClasses;
  final bool showLabels;
  final ValueChanged<double> onConfidenceChanged;
  final ValueChanged<Set<String>> onFilteredClassesChanged;
  final ValueChanged<bool> onShowLabelsChanged;
  final bool isCollapsed;
  final VoidCallback? onToggleCollapse;

  const DetectionControlPanel({
    Key? key,
    required this.detections,
    required this.minConfidence,
    required this.filteredClasses,
    required this.showLabels,
    required this.onConfidenceChanged,
    required this.onFilteredClassesChanged,
    required this.onShowLabelsChanged,
    this.isCollapsed = false,
    this.onToggleCollapse,
  }) : super(key: key);

  /// Get unique classes from detections
  List<String> get uniqueClasses {
    final classes = detections.map((d) => d.className).toSet().toList();
    classes.sort();
    return classes;
  }

  /// Get count of detections by class
  Map<String, int> get classCounts {
    final counts = <String, int>{};
    for (final detection in detections) {
      counts[detection.className] = (counts[detection.className] ?? 0) + 1;
    }
    return counts;
  }

  /// Get count of visible detections (after filtering)
  int get visibleCount {
    return detections.where((d) {
      if (d.confidence < minConfidence) return false;
      if (filteredClasses.isNotEmpty && !filteredClasses.contains(d.className)) {
        return false;
      }
      return true;
    }).length;
  }

  @override
  Widget build(BuildContext context) {
    if (isCollapsed) {
      return _buildCollapsedView(context);
    }

    return Card(
      margin: const EdgeInsets.all(8),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildHeader(context),
            const SizedBox(height: 12),
            _buildDetectionSummary(context),
            const SizedBox(height: 12),
            _buildConfidenceSlider(context),
            const SizedBox(height: 12),
            _buildClassFilters(context),
            const SizedBox(height: 8),
            _buildShowLabelsToggle(context),
          ],
        ),
      ),
    );
  }

  /// Build collapsed view showing just summary
  Widget _buildCollapsedView(BuildContext context) {
    return GestureDetector(
      onTap: onToggleCollapse,
      child: Card(
        margin: const EdgeInsets.all(8),
        elevation: 2,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.filter_list, size: 16),
              const SizedBox(width: 8),
              Text(
                '$visibleCount / ${detections.length} detections',
                style: const TextStyle(fontSize: 12),
              ),
              const SizedBox(width: 4),
              const Icon(Icons.expand_more, size: 16),
            ],
          ),
        ),
      ),
    );
  }

  /// Build header with title and collapse button
  Widget _buildHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          'Detection Filters',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        if (onToggleCollapse != null)
          IconButton(
            icon: const Icon(Icons.expand_less, size: 20),
            onPressed: onToggleCollapse,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
      ],
    );
  }

  /// Build detection summary showing counts
  Widget _buildDetectionSummary(BuildContext context) {
    final counts = classCounts;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Center the visible count text
        Center(
          child: Text(
            '$visibleCount / ${detections.length} visible',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        const SizedBox(height: 8),
        // Class counts
        Wrap(
          spacing: 8,
          runSpacing: 4,
          alignment: WrapAlignment.center,
          children: counts.entries.map((entry) {
            return Text(
              '${entry.key}: ${entry.value}',
              style: const TextStyle(fontSize: 15),
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Build confidence threshold slider
  Widget _buildConfidenceSlider(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Confidence Threshold',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
            ),
            Text(
              '${(minConfidence * 100).toInt()}%',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade700,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        Slider(
          value: minConfidence,
          min: 0.0,
          max: 1.0,
          divisions: 20,
          label: '${(minConfidence * 100).toInt()}%',
          onChanged: onConfidenceChanged,
        ),
      ],
    );
  }

  /// Build class filter chips
  Widget _buildClassFilters(BuildContext context) {
    final classes = uniqueClasses;

    if (classes.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Filter by Class',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
            ),
            if (filteredClasses.isNotEmpty)
              TextButton(
                onPressed: () => onFilteredClassesChanged({}),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  minimumSize: const Size(0, 24),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: const Text(
                  'Clear',
                  style: TextStyle(fontSize: 11),
                ),
              ),
          ],
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 6,
          runSpacing: 4,
          children: classes.map((className) {
            final isSelected = filteredClasses.isEmpty ||
                filteredClasses.contains(className);
            final count = classCounts[className] ?? 0;

            return FilterChip(
              label: Text(
                '$className ($count)',
                style: const TextStyle(fontSize: 11),
              ),
              selected: isSelected,
              onSelected: (selected) {
                final newFiltered = Set<String>.from(filteredClasses);
                if (selected) {
                  // If currently showing all, switch to only this class
                  if (filteredClasses.isEmpty) {
                    newFiltered.add(className);
                  } else {
                    newFiltered.add(className);
                  }
                } else {
                  newFiltered.remove(className);
                }
                onFilteredClassesChanged(newFiltered);
              },
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Build show labels toggle
  Widget _buildShowLabelsToggle(BuildContext context) {
    return SwitchListTile(
      title: const Text(
        'Show Labels',
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      ),
      value: showLabels,
      onChanged: onShowLabelsChanged,
      contentPadding: EdgeInsets.zero,
      dense: true,
    );
  }
}