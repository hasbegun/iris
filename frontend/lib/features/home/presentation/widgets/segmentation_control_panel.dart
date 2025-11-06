import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';

/// Control panel for filtering and adjusting segmentation visualization
class SegmentationControlPanel extends StatelessWidget {
  final List<Segment> segments;
  final double minConfidence;
  final Set<String> filteredClasses;
  final bool showLabels;
  final double opacity;
  final bool fillStyle;
  final ValueChanged<double> onConfidenceChanged;
  final ValueChanged<Set<String>> onFilteredClassesChanged;
  final ValueChanged<bool> onShowLabelsChanged;
  final ValueChanged<double> onOpacityChanged;
  final ValueChanged<bool> onFillStyleChanged;
  final bool isCollapsed;
  final VoidCallback? onToggleCollapse;

  const SegmentationControlPanel({
    Key? key,
    required this.segments,
    required this.minConfidence,
    required this.filteredClasses,
    required this.showLabels,
    required this.opacity,
    required this.fillStyle,
    required this.onConfidenceChanged,
    required this.onFilteredClassesChanged,
    required this.onShowLabelsChanged,
    required this.onOpacityChanged,
    required this.onFillStyleChanged,
    this.isCollapsed = false,
    this.onToggleCollapse,
  }) : super(key: key);

  /// Get unique classes from segments
  List<String> get uniqueClasses {
    final classes = segments.map((s) => s.className).toSet().toList();
    classes.sort();
    return classes;
  }

  /// Get count of segments by class
  Map<String, int> get classCounts {
    final counts = <String, int>{};
    for (final segment in segments) {
      counts[segment.className] = (counts[segment.className] ?? 0) + 1;
    }
    return counts;
  }

  /// Get count of visible segments (after filtering)
  int get visibleCount {
    return segments.where((s) {
      if (s.confidence < minConfidence) return false;
      if (filteredClasses.isNotEmpty && !filteredClasses.contains(s.className)) {
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
            _buildSegmentationSummary(context),
            const SizedBox(height: 12),
            _buildConfidenceSlider(context),
            const SizedBox(height: 12),
            _buildOpacitySlider(context),
            const SizedBox(height: 12),
            _buildClassFilters(context),
            const SizedBox(height: 8),
            _buildShowLabelsToggle(context),
            _buildFillStyleToggle(context),
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
              const Icon(Icons.tune, size: 16),
              const SizedBox(width: 8),
              Text(
                '$visibleCount / ${segments.length} segments',
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
          'Segmentation Controls',
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

  /// Build segmentation summary showing counts
  Widget _buildSegmentationSummary(BuildContext context) {
    final counts = classCounts;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Center the visible count text
        Center(
          child: Text(
            '$visibleCount / ${segments.length} visible',
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

  /// Build opacity slider
  Widget _buildOpacitySlider(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Mask Opacity',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
            ),
            Text(
              '${(opacity * 100).toInt()}%',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade700,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        Slider(
          value: opacity,
          min: 0.0,
          max: 1.0,
          divisions: 20,
          label: '${(opacity * 100).toInt()}%',
          onChanged: onOpacityChanged,
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

  /// Build fill style toggle (filled vs outline only)
  Widget _buildFillStyleToggle(BuildContext context) {
    return SwitchListTile(
      title: const Text(
        'Fill Masks',
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      ),
      value: fillStyle,
      onChanged: onFillStyleChanged,
      contentPadding: EdgeInsets.zero,
      dense: true,
    );
  }
}
