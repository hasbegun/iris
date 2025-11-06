import 'package:flutter_test/flutter_test.dart';
import 'package:iris/features/api/models/detection.dart';
import 'package:iris/features/api/models/vision_response.dart';

void main() {
  group('Detection Model Tests', () {
    test('Detection.fromJson parses correctly', () {
      final json = {
        'class_name': 'car',
        'confidence': 0.89,
        'bbox': [120.5, 200.3, 450.2, 380.7]
      };

      final detection = Detection.fromJson(json);

      expect(detection.className, 'car');
      expect(detection.confidence, 0.89);
      expect(detection.bbox, [120.5, 200.3, 450.2, 380.7]);
      expect(detection.x1, 120.5);
      expect(detection.y1, 200.3);
      expect(detection.x2, 450.2);
      expect(detection.y2, 380.7);
      expect(detection.width, 450.2 - 120.5);
      expect(detection.height, 380.7 - 200.3);
      expect(detection.isValid, true);
    });

    test('Detection.toJson serializes correctly', () {
      final detection = Detection(
        className: 'person',
        confidence: 0.92,
        bbox: [100.0, 150.0, 200.0, 400.0],
      );

      final json = detection.toJson();

      expect(json['class_name'], 'person');
      expect(json['confidence'], 0.92);
      expect(json['bbox'], [100.0, 150.0, 200.0, 400.0]);
    });

    test('Detection center calculation', () {
      final detection = Detection(
        className: 'dog',
        confidence: 0.85,
        bbox: [0.0, 0.0, 100.0, 200.0],
      );

      final center = detection.center;
      expect(center.$1, 50.0); // x center
      expect(center.$2, 100.0); // y center
    });
  });

  group('ImageMetadata Model Tests', () {
    test('ImageMetadata.fromJson parses correctly', () {
      final json = {'width': 1920, 'height': 1080};

      final metadata = ImageMetadata.fromJson(json);

      expect(metadata.width, 1920);
      expect(metadata.height, 1080);
      expect(metadata.aspectRatio, closeTo(1.777, 0.01));
      expect(metadata.isValid, true);
    });

    test('ImageMetadata.toJson serializes correctly', () {
      final metadata = ImageMetadata(width: 800, height: 600);

      final json = metadata.toJson();

      expect(json['width'], 800);
      expect(json['height'], 600);
    });
  });

  group('VisionResponse with Detections Tests', () {
    test('VisionResponse.fromJson with detections parses correctly', () {
      final json = {
        'session_id': 'test-123',
        'response': 'I found 2 cars in the image',
        'model_used': 'llama3',
        'processing_time': 1.5,
        'annotated_image_url': '/api/images/test.jpg',
        'has_annotated_image': true,
        'detections': [
          {
            'class_name': 'car',
            'confidence': 0.89,
            'bbox': [100.0, 200.0, 300.0, 400.0]
          },
          {
            'class_name': 'car',
            'confidence': 0.85,
            'bbox': [500.0, 200.0, 700.0, 400.0]
          },
        ],
        'image_metadata': {'width': 1920, 'height': 1080}
      };

      final response = VisionResponse.fromJson(json);

      expect(response.sessionId, 'test-123');
      expect(response.response, 'I found 2 cars in the image');
      expect(response.hasDetections, true);
      expect(response.detections, isNotNull);
      expect(response.detections!.length, 2);
      expect(response.imageMetadata, isNotNull);
      expect(response.imageMetadata!.width, 1920);
      expect(response.imageMetadata!.height, 1080);
      expect(response.totalDetections, 2);
    });

    test('VisionResponse.detectionCounts groups correctly', () {
      final json = {
        'session_id': 'test-456',
        'response': 'Found multiple objects',
        'model_used': 'llama3',
        'processing_time': 2.0,
        'detections': [
          {
            'class_name': 'car',
            'confidence': 0.89,
            'bbox': [100.0, 200.0, 300.0, 400.0]
          },
          {
            'class_name': 'car',
            'confidence': 0.85,
            'bbox': [500.0, 200.0, 700.0, 400.0]
          },
          {
            'class_name': 'person',
            'confidence': 0.92,
            'bbox': [200.0, 100.0, 300.0, 400.0]
          },
        ],
        'image_metadata': {'width': 1920, 'height': 1080}
      };

      final response = VisionResponse.fromJson(json);

      final counts = response.detectionCounts;
      expect(counts['car'], 2);
      expect(counts['person'], 1);
      expect(response.totalDetections, 3);
    });

    test('VisionResponse without detections', () {
      final json = {
        'session_id': 'test-789',
        'response': 'This is a general description',
        'model_used': 'llama3',
        'processing_time': 1.0,
      };

      final response = VisionResponse.fromJson(json);

      expect(response.hasDetections, false);
      expect(response.detections, isNull);
      expect(response.imageMetadata, isNull);
      expect(response.totalDetections, 0);
      expect(response.detectionCounts, isEmpty);
    });

    test('VisionResponse.toJson with detections serializes correctly', () {
      final response = VisionResponse(
        sessionId: 'test-abc',
        response: 'Found 1 dog',
        modelUsed: 'llama3',
        processingTime: 1.2,
        detections: [
          Detection(
            className: 'dog',
            confidence: 0.95,
            bbox: [100.0, 100.0, 300.0, 400.0],
          ),
        ],
        imageMetadata: ImageMetadata(width: 800, height: 600),
      );

      final json = response.toJson();

      expect(json['session_id'], 'test-abc');
      expect(json['detections'], isNotNull);
      expect((json['detections'] as List).length, 1);
      expect(json['image_metadata'], isNotNull);
      expect((json['image_metadata'] as Map)['width'], 800);
    });
  });
}
