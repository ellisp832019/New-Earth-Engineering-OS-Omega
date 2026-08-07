import 'dart:convert';

import 'package:http/http.dart' as http;

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) {
    return value;
  }
  if (value is Map) {
    return value.map((key, item) => MapEntry(key.toString(), item));
  }
  return <String, dynamic>{};
}

List<dynamic> _list(dynamic value) {
  if (value is List) {
    return value;
  }
  return const <dynamic>[];
}

String _string(dynamic value, [String fallback = '']) {
  return value == null ? fallback : value.toString();
}

int _int(dynamic value, [int fallback = 0]) {
  if (value is int) {
    return value;
  }
  return int.tryParse(_string(value)) ?? fallback;
}

class ServiceOverview {
  const ServiceOverview({
    required this.health,
    required this.projects,
  });

  factory ServiceOverview.fromResponses({
    required Map<String, dynamic> health,
    required Map<String, dynamic> projects,
  }) {
    final items = _list(projects['projects']).map((value) => ProjectOverview.fromJson(_map(value))).toList(growable: false);
    return ServiceOverview(
      health: health,
      projects: items,
    );
  }

  final Map<String, dynamic> health;
  final List<ProjectOverview> projects;

  String get serviceName => _string(health['service_name'], 'NEOS Local Service');
  String get apiVersion => _string(health['api_version'], 'v1');
  String get status => _string(health['status'], 'unknown');
  String get host => _string(health['host'], '127.0.0.1');
  int get port => _int(health['port'], 8765);
  String get dbPath => _string(health['db_path'], '');
  int get registeredProjects => _int(health['registered_projects'], projects.length);
  int get databaseSizeBytes => _int(health['database_size_bytes']);
  Map<String, dynamic> get schema => _map(health['schema']);
  Map<String, dynamic> get lastScan => _map(health['last_scan']);
}

class ProjectOverview {
  const ProjectOverview({
    required this.projectId,
    required this.name,
    required this.repoPath,
    required this.branch,
    required this.commit,
    required this.scanId,
    required this.scanFreshness,
    required this.lastAnalysisTime,
    required this.health,
    required this.genomeStatus,
    required this.memoryStatus,
    required this.flightStatus,
    required this.summary,
  });

  factory ProjectOverview.fromJson(Map<String, dynamic> json) {
    return ProjectOverview(
      projectId: _string(json['project_id']),
      name: _string(json['name'], _string(json['project_id'])),
      repoPath: _string(json['repo_path']),
      branch: _string(json['branch'], 'unknown'),
      commit: _string(json['commit']),
      scanId: _string(json['scan_id']),
      scanFreshness: _string(json['scan_freshness'], 'unknown'),
      lastAnalysisTime: _string(json['last_analysis_time']),
      health: _map(json['health']),
      genomeStatus: _string(json['genome_status'], 'missing'),
      memoryStatus: _string(json['memory_status'], 'missing'),
      flightStatus: _string(json['flight_status'], 'missing'),
      summary: _map(json['summary']),
    );
  }

  final String projectId;
  final String name;
  final String repoPath;
  final String branch;
  final String commit;
  final String scanId;
  final String scanFreshness;
  final String lastAnalysisTime;
  final Map<String, dynamic> health;
  final String genomeStatus;
  final String memoryStatus;
  final String flightStatus;
  final Map<String, dynamic> summary;
}

class ProjectRecord {
  const ProjectRecord({
    required this.projectId,
    required this.payload,
  });

  factory ProjectRecord.fromJson(Map<String, dynamic> json) {
    return ProjectRecord(
      projectId: _string(_map(json['project'])['project_id'], _string(json['project_id'])),
      payload: json,
    );
  }

  final String projectId;
  final Map<String, dynamic> payload;

  Map<String, dynamic> get project => _map(payload['project']);
  Map<String, dynamic> get summary => _map(payload['summary']);
  Map<String, dynamic> get genome => _map(payload['genome']);
  Map<String, dynamic> get memory => _map(payload['memory']);
  Map<String, dynamic> get flight => _map(payload['flight']);

  Map<String, dynamic> section(String key) => _map(payload[key]);
  int count(String key) {
    final value = payload[key];
    if (value is Map<String, dynamic> && value['count'] is int) {
      return value['count'] as int;
    }
    if (value is Map && value['count'] is int) {
      return value['count'] as int;
    }
    if (value is Map && value['items'] is List) {
      return (value['items'] as List).length;
    }
    if (value is List) {
      return value.length;
    }
    return 0;
  }

  List<dynamic> items(String key) {
    final value = payload[key];
    if (value is Map && value['items'] is List) {
      return value['items'] as List<dynamic>;
    }
    if (value is List) {
      return value;
    }
    return const <dynamic>[];
  }
}

abstract class NeosClient {
  Future<ServiceOverview> loadOverview(Uri baseUri);
  Future<ProjectRecord> loadProject(Uri baseUri, String projectId);
}

class HttpNeosClient implements NeosClient {
  HttpNeosClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Future<Map<String, dynamic>> _getJson(Uri uri) async {
    final response = await _client.get(uri).timeout(const Duration(seconds: 10));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('NEOS service responded with ${response.statusCode} for $uri');
    }
    final decoded = jsonDecode(response.body);
    return _map(decoded);
  }

  @override
  Future<ServiceOverview> loadOverview(Uri baseUri) async {
    final normalized = _normalize(baseUri);
    final results = await Future.wait([
      _getJson(normalized.resolve('health')),
      _getJson(normalized.resolve('projects')),
    ]);
    return ServiceOverview.fromResponses(health: results[0], projects: results[1]);
  }

  @override
  Future<ProjectRecord> loadProject(Uri baseUri, String projectId) async {
    final normalized = _normalize(baseUri);
    final json = await _getJson(normalized.resolve('projects/$projectId'));
    return ProjectRecord.fromJson(json);
  }

  Uri _normalize(Uri baseUri) {
    final text = baseUri.toString();
    if (text.endsWith('/')) {
      return baseUri;
    }
    return Uri.parse('$text/');
  }
}
