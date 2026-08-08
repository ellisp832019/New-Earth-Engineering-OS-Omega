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

class ServiceHealthInfo {
  const ServiceHealthInfo({
    required this.raw,
  });

  factory ServiceHealthInfo.fromJson(Map<String, dynamic> json) {
    return ServiceHealthInfo(raw: json);
  }

  final Map<String, dynamic> raw;

  String get status => _string(raw['status'], 'unknown');
  String get serviceName => _string(raw['service_name'], 'NEOS Local Service');
  String get serviceVersion => _string(raw['service_version'], '0.7.0');
  String get apiVersion => _string(raw['api_version'], 'v1');
  int get schemaVersion => _int(raw['schema_version'], _int(_map(raw['schema'])['database_schema'], 0));
  String get instanceId => _string(raw['instance_id']);
  int? get ownerPid => raw['owner_pid'] is int ? raw['owner_pid'] as int : null;
  String get host => _string(raw['host'], '127.0.0.1');
  int get port => _int(raw['port'], 8765);
  bool get isNeos => serviceName.toLowerCase().contains('neos') && apiVersion == 'v1';
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

class AIProviderSummary {
  const AIProviderSummary({
    required this.providerId,
    required this.name,
    required this.kind,
    required this.configured,
    required this.local,
    required this.healthy,
    required this.model,
    required this.endpoint,
    required this.message,
  });

  factory AIProviderSummary.fromJson(Map<String, dynamic> json) {
    return AIProviderSummary(
      providerId: _string(json['provider_id']),
      name: _string(json['name']),
      kind: _string(json['kind']),
      configured: json['configured'] == true,
      local: json['local'] == true,
      healthy: json['healthy'] == true,
      model: _string(json['model']),
      endpoint: _string(json['endpoint']),
      message: _string(json['message']),
    );
  }

  final String providerId;
  final String name;
  final String kind;
  final bool configured;
  final bool local;
  final bool healthy;
  final String model;
  final String endpoint;
  final String message;
}

class AIConversationSummary {
  const AIConversationSummary({
    required this.conversationId,
    required this.projectId,
    required this.title,
    required this.providerId,
    required this.model,
    required this.status,
    required this.turnCount,
    required this.createdAt,
    required this.updatedAt,
  });

  factory AIConversationSummary.fromJson(Map<String, dynamic> json) {
    return AIConversationSummary(
      conversationId: _string(json['conversation_id']),
      projectId: _string(json['project_id']),
      title: _string(json['title']),
      providerId: _string(json['provider_id']),
      model: _string(json['model']),
      status: _string(json['status']),
      turnCount: _int(json['turn_count']),
      createdAt: _string(json['created_at']),
      updatedAt: _string(json['updated_at']),
    );
  }

  final String conversationId;
  final String projectId;
  final String title;
  final String providerId;
  final String model;
  final String status;
  final int turnCount;
  final String createdAt;
  final String updatedAt;
}

abstract class NeosClient {
  Future<ServiceHealthInfo> probeHealth(Uri baseUri);
  Future<ServiceOverview> loadOverview(Uri baseUri);
  Future<ProjectRecord> loadProject(Uri baseUri, String projectId);
  Future<Map<String, dynamic>> loadEcosystem(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemProjects(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemCapabilities(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemTechnologies(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemReuse(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemDuplication(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemDependencies(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemRisks(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemUnknowns(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemAttention(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemTimeline(Uri baseUri);
  Future<Map<String, dynamic>> searchEcosystem(Uri baseUri, String query, {List<String>? projectIds, int limit = 20, int offset = 0});
  Future<Map<String, dynamic>> loadEcosystemSnapshot(Uri baseUri);
  Future<Map<String, dynamic>> loadEcosystemDiff(Uri baseUri, String fromSnapshotId, String toSnapshotId);
  Future<Map<String, dynamic>> registerProject(Uri baseUri, String manifestPath);
  Future<Map<String, dynamic>> scanProject(Uri baseUri, String projectId, {String? repoPath});
  Future<Map<String, dynamic>> shutdownService(Uri baseUri, String shutdownToken);
  Future<Map<String, dynamic>> loadAiSettings(Uri baseUri);
  Future<Map<String, dynamic>> saveAiSettings(Uri baseUri, Map<String, dynamic> settings);
  Future<List<AIProviderSummary>> loadAiProviders(Uri baseUri);
  Future<List<AIConversationSummary>> loadAiConversations(Uri baseUri, {String? projectId});
  Future<Map<String, dynamic>> createAiConversation(Uri baseUri, {required String projectId, required String title});
  Future<Map<String, dynamic>> loadAiConversation(Uri baseUri, String conversationId);
  Future<Map<String, dynamic>> askAi(Uri baseUri, {required String projectId, required String question, List<String>? projectIds, String? conversationId, String? mode});
  Future<Map<String, dynamic>> loadAiRequest(Uri baseUri, String requestId);
  Future<Map<String, dynamic>> loadAiRequestCitations(Uri baseUri, String requestId);
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

  Future<Map<String, dynamic>> _postJson(Uri uri, Map<String, dynamic> body) async {
    final response = await _client
        .post(
          uri,
          headers: const {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 10));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('NEOS service responded with ${response.statusCode} for $uri');
    }
    final decoded = jsonDecode(response.body);
    return _map(decoded);
  }

  @override
  Future<ServiceHealthInfo> probeHealth(Uri baseUri) async {
    final normalized = _normalize(baseUri);
    return ServiceHealthInfo.fromJson(await _getJson(normalized.resolve('health')));
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

  @override
  Future<Map<String, dynamic>> loadEcosystem(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem'));

  @override
  Future<Map<String, dynamic>> loadEcosystemProjects(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/projects'));

  @override
  Future<Map<String, dynamic>> loadEcosystemCapabilities(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/capabilities'));

  @override
  Future<Map<String, dynamic>> loadEcosystemTechnologies(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/technologies'));

  @override
  Future<Map<String, dynamic>> loadEcosystemReuse(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/reuse'));

  @override
  Future<Map<String, dynamic>> loadEcosystemDuplication(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/duplication'));

  @override
  Future<Map<String, dynamic>> loadEcosystemDependencies(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/dependencies'));

  @override
  Future<Map<String, dynamic>> loadEcosystemRisks(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/risks'));

  @override
  Future<Map<String, dynamic>> loadEcosystemUnknowns(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/unknowns'));

  @override
  Future<Map<String, dynamic>> loadEcosystemAttention(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/attention'));

  @override
  Future<Map<String, dynamic>> loadEcosystemTimeline(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/timeline'));

  @override
  Future<Map<String, dynamic>> searchEcosystem(Uri baseUri, String query, {List<String>? projectIds, int limit = 20, int offset = 0}) async {
    final normalized = _normalize(baseUri);
    final params = <String, String>{
      'q': query,
      'limit': '$limit',
      'offset': '$offset',
    };
    final queryParts = params.entries
        .map((entry) => '${Uri.encodeQueryComponent(entry.key)}=${Uri.encodeQueryComponent(entry.value)}')
        .toList(growable: true);
    if (projectIds != null && projectIds.isNotEmpty) {
      queryParts.addAll(projectIds.map((value) => 'project_id=${Uri.encodeQueryComponent(value)}'));
    }
    final uri = Uri.parse('${normalized.toString()}ecosystem/search?${queryParts.join('&')}');
    return _getJson(uri);
  }

  @override
  Future<Map<String, dynamic>> loadEcosystemSnapshot(Uri baseUri) async => _getJson(_normalize(baseUri).resolve('ecosystem/snapshot'));

  @override
  Future<Map<String, dynamic>> loadEcosystemDiff(Uri baseUri, String fromSnapshotId, String toSnapshotId) async =>
      _getJson(_normalize(baseUri).resolve('ecosystem/diff/$fromSnapshotId/$toSnapshotId'));

  @override
  Future<Map<String, dynamic>> registerProject(Uri baseUri, String manifestPath) async {
    final normalized = _normalize(baseUri);
    return _postJson(normalized.resolve('projects/register'), {'manifest_path': manifestPath});
  }

  @override
  Future<Map<String, dynamic>> scanProject(Uri baseUri, String projectId, {String? repoPath}) async {
    final normalized = _normalize(baseUri);
    final body = <String, dynamic>{};
    if (repoPath != null && repoPath.isNotEmpty) {
      body['repo_path'] = repoPath;
    }
    return _postJson(normalized.resolve('projects/$projectId/scan'), body);
  }

  @override
  Future<Map<String, dynamic>> shutdownService(Uri baseUri, String shutdownToken) async {
    final normalized = _normalize(baseUri);
    return _postJson(normalized.resolve('shutdown'), {'shutdown_token': shutdownToken});
  }

  @override
  Future<Map<String, dynamic>> loadAiSettings(Uri baseUri) async {
    final normalized = _normalize(baseUri);
    return _getJson(normalized.resolve('ai/settings'));
  }

  @override
  Future<Map<String, dynamic>> saveAiSettings(Uri baseUri, Map<String, dynamic> settings) async {
    final normalized = _normalize(baseUri);
    return _postJson(normalized.resolve('ai/settings'), settings);
  }

  @override
  Future<List<AIProviderSummary>> loadAiProviders(Uri baseUri) async {
    final normalized = _normalize(baseUri);
    final json = await _getJson(normalized.resolve('ai/providers'));
    return _list(json['providers']).map((value) => AIProviderSummary.fromJson(_map(value))).toList(growable: false);
  }

  @override
  Future<List<AIConversationSummary>> loadAiConversations(Uri baseUri, {String? projectId}) async {
    final normalized = _normalize(baseUri);
    final uri = projectId == null || projectId.isEmpty
        ? normalized.resolve('ai/conversations')
        : normalized.resolve('ai/conversations?project_id=${Uri.encodeQueryComponent(projectId)}');
    final json = await _getJson(uri);
    return _list(json['conversations']).map((value) => AIConversationSummary.fromJson(_map(value))).toList(growable: false);
  }

  @override
  Future<Map<String, dynamic>> createAiConversation(Uri baseUri, {required String projectId, required String title}) async {
    final normalized = _normalize(baseUri);
    return _postJson(normalized.resolve('ai/conversations'), {'project_id': projectId, 'title': title});
  }

  @override
  Future<Map<String, dynamic>> loadAiConversation(Uri baseUri, String conversationId) async {
    final normalized = _normalize(baseUri);
    return _getJson(normalized.resolve('ai/conversations/$conversationId'));
  }

  @override
  Future<Map<String, dynamic>> askAi(Uri baseUri, {required String projectId, required String question, List<String>? projectIds, String? conversationId, String? mode}) async {
    final normalized = _normalize(baseUri);
    final body = <String, dynamic>{
      'project_id': projectId,
      'question': question,
    };
    if (projectIds != null && projectIds.isNotEmpty) {
      body['project_ids'] = projectIds;
    }
    if (conversationId != null && conversationId.isNotEmpty) {
      body['conversation_id'] = conversationId;
    }
    if (mode != null && mode.isNotEmpty) {
      body['mode'] = mode;
    }
    return _postJson(normalized.resolve('ai/query'), body);
  }

  @override
  Future<Map<String, dynamic>> loadAiRequest(Uri baseUri, String requestId) async {
    final normalized = _normalize(baseUri);
    return _getJson(normalized.resolve('ai/requests/$requestId'));
  }

  @override
  Future<Map<String, dynamic>> loadAiRequestCitations(Uri baseUri, String requestId) async {
    final normalized = _normalize(baseUri);
    return _getJson(normalized.resolve('ai/requests/$requestId/citations'));
  }

  Uri _normalize(Uri baseUri) {
    final text = baseUri.toString();
    if (text.endsWith('/')) {
      return baseUri;
    }
    return Uri.parse('$text/');
  }
}
