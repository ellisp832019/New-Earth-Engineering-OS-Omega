import 'package:desktop/app.dart';
import 'package:desktop/neos_client.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeNeosClient implements NeosClient {
  @override
  Future<ServiceHealthInfo> probeHealth(Uri baseUri) async {
    return ServiceHealthInfo.fromJson({
      'status': 'healthy',
      'service_name': 'NEOS Local Service',
      'service_version': '0.7.0',
      'api_version': 'v1',
      'schema_version': 8,
      'instance_id': 'fake-instance',
      'owner_pid': 0,
      'host': '127.0.0.1',
      'port': 8765,
    });
  }

  @override
  Future<ProjectRecord> loadProject(Uri baseUri, String projectId) async {
    return ProjectRecord.fromJson({
      'project': {
        'project_id': projectId,
        'name': 'Demo Project',
      },
      'summary': {
        'name': 'Demo Project',
        'status': 'healthy',
      },
      'genome': {'project_id': projectId, 'maturity': {'status': 'stable'}},
      'memory': {'project_id': projectId, 'summary': {'decisions': 1}},
      'flight': {'project_id': projectId, 'status': 'available'},
      'dependencies': {'count': 1, 'items': ['demo -> core']},
      'documentation': {'count': 2, 'items': ['README.md', 'GUIDE.md']},
      'tests': {'count': 1, 'items': ['test_demo.py']},
      'apis': {'count': 1, 'items': ['GET /health']},
      'symbols': {'count': 1, 'items': ['DemoClass']},
      'features': {'count': 1, 'items': ['feature-1']},
      'decisions': {'count': 1, 'items': ['decision-1']},
      'configuration': {'count': 1, 'items': ['config-1']},
      'build': {'count': 1, 'items': ['build-1']},
      'why': {'answers': []},
      'trace': {'nodes': []},
      'impact': {'nodes': []},
      'flight_timeline': {'count': 0, 'items': []},
      'flight_snapshots': {'count': 0, 'items': []},
      'flight_incidents': {'count': 0, 'items': []},
      'flight_regressions': {'count': 0, 'items': []},
      'memory_timeline': {'count': 0, 'items': []},
    });
  }

  @override
  Future<ServiceOverview> loadOverview(Uri baseUri) async {
    return ServiceOverview.fromResponses(
      health: {
        'status': 'healthy',
        'service_name': 'NEOS Local Service',
        'api_version': 'v1',
        'host': '127.0.0.1',
        'port': 8765,
        'db_path': 'C:/neos.db',
        'database_size_bytes': 1024,
        'registered_projects': 1,
        'schema': {'database_schema': 8},
        'last_scan': {'created_at': '2026-08-07T00:00:00Z'},
      },
      projects: {
        'projects': [
          {
            'project_id': 'demo',
            'name': 'Demo Project',
            'repo_path': 'C:/demo',
            'branch': 'main',
            'commit': 'abc123',
            'scan_id': 'scan-1',
            'scan_freshness': 'fresh',
            'last_analysis_time': '2026-08-07T00:00:00Z',
            'health': {'status': 'healthy'},
            'genome_status': 'available',
            'memory_status': 'available',
            'flight_status': 'available',
            'summary': {'name': 'Demo Project'},
          },
        ],
      },
    );
  }

  @override
  Future<Map<String, dynamic>> registerProject(Uri baseUri, String manifestPath) async {
    return {'status': 'registered', 'project_id': 'demo'};
  }

  @override
  Future<Map<String, dynamic>> scanProject(Uri baseUri, String projectId, {String? repoPath}) async {
    return {'status': 'scanned', 'project_id': projectId};
  }

  @override
  Future<Map<String, dynamic>> shutdownService(Uri baseUri, String shutdownToken) async {
    return {'status': 'shutting_down'};
  }

  @override
  Future<Map<String, dynamic>> loadAiSettings(Uri baseUri) async {
    return {
      'settings': {
        'provider_id': 'mock',
        'model': 'mock-engineer-v1',
        'endpoint': '',
        'timeout_seconds': 30,
        'context_budget': 24,
        'max_output_tokens': 1200,
        'streaming': false,
      },
      'provider': {
        'provider_id': 'mock',
        'name': 'Local Mock Provider',
        'kind': 'local',
        'configured': true,
        'local': true,
        'healthy': true,
        'model': 'mock-engineer-v1',
        'endpoint': '',
        'message': 'Deterministic local mock provider ready.',
      },
      'provider_health': {
        'configured': true,
        'healthy': true,
        'message': 'Deterministic local mock provider ready.',
      },
    };
  }

  @override
  Future<Map<String, dynamic>> saveAiSettings(Uri baseUri, Map<String, dynamic> settings) async {
    return loadAiSettings(baseUri);
  }

  @override
  Future<List<AIProviderSummary>> loadAiProviders(Uri baseUri) async {
    return [
      AIProviderSummary.fromJson({
        'provider_id': 'mock',
        'name': 'Local Mock Provider',
        'kind': 'local',
        'configured': true,
        'local': true,
        'healthy': true,
        'model': 'mock-engineer-v1',
        'endpoint': '',
        'message': 'Deterministic local mock provider ready.',
      }),
    ];
  }

  @override
  Future<List<AIConversationSummary>> loadAiConversations(Uri baseUri, {String? projectId}) async {
    return const [];
  }

  @override
  Future<Map<String, dynamic>> createAiConversation(Uri baseUri, {required String projectId, required String title}) async {
    return {
      'conversation_id': 'conversation-1',
      'project_id': projectId,
      'title': title,
      'provider_id': 'mock',
      'model': 'mock-engineer-v1',
      'status': 'active',
      'created_at': '2026-08-07T00:00:00Z',
      'updated_at': '2026-08-07T00:00:00Z',
      'turn_count': 0,
      'turns': const [],
    };
  }

  @override
  Future<Map<String, dynamic>> loadAiConversation(Uri baseUri, String conversationId) async {
    return {
      'conversation_id': conversationId,
      'project_id': 'demo',
      'title': 'Demo Conversation',
      'provider_id': 'mock',
      'model': 'mock-engineer-v1',
      'status': 'active',
      'created_at': '2026-08-07T00:00:00Z',
      'updated_at': '2026-08-07T00:00:00Z',
      'turn_count': 1,
      'turns': [
        {
          'turn_id': 'turn-1',
          'request_id': 'request-1',
          'conversation_id': conversationId,
          'project_id': 'demo',
          'question': 'What should I work on next?',
          'response_json': {
            'request_id': 'request-1',
            'conversation_id': conversationId,
            'project_id': 'demo',
            'question': 'What should I work on next?',
            'intent': 'plan',
            'mode': 'plan',
            'provider': 'mock',
            'model': 'mock-engineer-v1',
            'created_at': '2026-08-07T00:00:00Z',
            'completed_at': '2026-08-07T00:00:01Z',
            'status': 'success',
            'answer': 'Focus on the highest-attention evidence.',
            'facts': [],
            'derived_facts': [],
            'inferences': [],
            'recommendations': [],
            'unknowns': [],
            'citations': [],
            'context_snapshot': {'project_id': 'demo'},
            'latency_ms': 1,
            'usage': {'total_tokens': 1},
            'safety': [],
            'tool_calls': [],
            'confidence': 'medium',
          },
          'context_json': {'project_id': 'demo'},
          'citations_json': const [],
          'provider_id': 'mock',
          'model': 'mock-engineer-v1',
          'intent': 'plan',
          'mode': 'plan',
          'status': 'success',
          'created_at': '2026-08-07T00:00:00Z',
          'completed_at': '2026-08-07T00:00:01Z',
          'usage_json': {'total_tokens': 1},
          'safety_json': const [],
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> askAi(Uri baseUri, {required String projectId, required String question, String? conversationId, String? mode}) async {
    return {
      'request_id': 'request-1',
      'conversation_id': conversationId ?? 'conversation-1',
      'project_id': projectId,
      'question': question,
      'intent': mode ?? 'plan',
      'mode': mode ?? 'plan',
      'provider': 'mock',
      'model': 'mock-engineer-v1',
      'created_at': '2026-08-07T00:00:00Z',
      'completed_at': '2026-08-07T00:00:01Z',
      'status': 'success',
      'answer': 'Focus on the highest-attention evidence.',
      'facts': [],
      'derived_facts': [],
      'inferences': [],
      'recommendations': [],
      'unknowns': [],
      'citations': const [],
      'context_snapshot': {'project_id': projectId, 'evidence_items': []},
      'latency_ms': 1,
      'usage': {'total_tokens': 1},
      'safety': const [],
      'tool_calls': const [],
      'confidence': 'medium',
    };
  }

  @override
  Future<Map<String, dynamic>> loadAiRequest(Uri baseUri, String requestId) async {
    return {'request_id': requestId, 'status': 'success'};
  }

  @override
  Future<Map<String, dynamic>> loadAiRequestCitations(Uri baseUri, String requestId) async {
    return {'request_id': requestId, 'count': 0, 'citations': const []};
  }
}

void main() {
  testWidgets('NEOS shell renders the desktop workspace', (WidgetTester tester) async {
    await tester.pumpWidget(NeosApp(client: FakeNeosClient()));
    await tester.pumpAndSettle();

    expect(find.text('Windows desktop engineering shell'), findsOneWidget);
    expect(find.byIcon(Icons.home_outlined), findsOneWidget);
    expect(find.text('Demo Project'), findsWidgets);
    expect(find.text('Navigation'), findsOneWidget);
  });
}
