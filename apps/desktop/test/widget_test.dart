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
      'service_version': '0.9.0',
      'api_version': 'v1',
      'schema_version': 10,
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
      'requirements': {'count': 1, 'items': [{'id': 'req-1', 'title': 'Select a project'}]},
      'requirement_gaps': {'count': 1, 'items': [{'requirement_id': 'req-1', 'gaps': ['no_test_evidence']}]},
      'requirement_verification': {'count': 0, 'items': []},
      'requirement_architecture_gaps': {'count': 0, 'items': []},
      'requirement_unimplemented': {'count': 0, 'items': []},
      'requirement_untested': {'count': 1, 'items': [{'requirement_id': 'req-1'}]},
      'requirement_history': {'count': 1, 'items': [{'id': 'req-1', 'review_state': 'confirmed'}]},
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
        'schema': {'database_schema': 10},
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
  Future<Map<String, dynamic>> loadEcosystem(Uri baseUri) async {
    return {
      'ecosystem': {'id': 'ecosystem-1', 'name': 'Demo Ecosystem'},
      'projects': [
        {'project_id': 'demo'},
      ],
      'health': {'score': 75},
      'technology_portfolio': {'technologies': const []},
      'capability_matrix': {'shared_capabilities': const []},
      'reuse_candidates': const [],
      'duplicate_findings': const [],
      'cross_project_dependencies': const [],
      'portfolio_risks': const [],
      'unknown_surface': const [],
      'attention': const [],
    };
  }

  @override
  Future<Map<String, dynamic>> loadEcosystemProjects(Uri baseUri) async {
    return {
      'count': 1,
      'projects': [
        {'project_id': 'demo', 'display_name': 'Demo Project'},
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> loadEcosystemCapabilities(Uri baseUri) async => {'shared_capabilities': const [], 'project_capabilities': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemTechnologies(Uri baseUri) async => {'technologies': const [], 'shared_technologies': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemReuse(Uri baseUri) async => {'count': 0, 'items': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemDuplication(Uri baseUri) async => {'count': 0, 'items': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemDependencies(Uri baseUri) async => {'count': 0, 'items': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemRisks(Uri baseUri) async => {'count': 0, 'items': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemUnknowns(Uri baseUri) async => {'count': 0, 'items': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemAttention(Uri baseUri) async => {'count': 0, 'items': const []};

  @override
  Future<Map<String, dynamic>> loadEcosystemTimeline(Uri baseUri) async => {'count': 0, 'items': const []};

  @override
  Future<Map<String, dynamic>> searchEcosystem(Uri baseUri, String query, {List<String>? projectIds, int limit = 20, int offset = 0}) async {
    return {'query': query, 'count': 0, 'items': const []};
  }

  @override
  Future<Map<String, dynamic>> loadEcosystemSnapshot(Uri baseUri) async => {'error': 'not_found'};

  @override
  Future<Map<String, dynamic>> loadEcosystemDiff(Uri baseUri, String fromSnapshotId, String toSnapshotId) async {
    return {'from_snapshot_id': fromSnapshotId, 'to_snapshot_id': toSnapshotId, 'added_projects': const [], 'removed_projects': const [], 'changed_projects': const []};
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
  Future<Map<String, dynamic>> askAi(Uri baseUri, {required String projectId, required String question, List<String>? projectIds, String? conversationId, String? mode}) async {
    return {
      'request_id': 'request-1',
      'conversation_id': conversationId ?? 'conversation-1',
      'project_id': projectId,
      'project_ids': projectIds ?? <String>[projectId],
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

  @override
  Future<Map<String, dynamic>> loadRequirementIntelligence(Uri baseUri, {List<String>? projectIds}) async {
    return {
      'project_count': 1,
      'requirement_count': 1,
      'requirements': [
        {'id': 'req-1', 'project_id': 'demo', 'title': 'Select a project', 'status': 'verified'},
      ],
      'gaps': const [],
      'architecture_without_requirement': const [],
      'verification_ready': const [],
      'summary': {'candidate_count': 1, 'evidence_count': 1},
    };
  }

  @override
  Future<Map<String, dynamic>> loadRequirementInventory(Uri baseUri, {List<String>? projectIds}) async {
    return {'count': 1, 'items': [{'id': 'req-1', 'project_id': 'demo', 'title': 'Select a project'}]};
  }

  @override
  Future<Map<String, dynamic>> loadRequirementShow(Uri baseUri, String requirementId) async {
    return {
      'requirement': {'id': requirementId, 'project_id': 'demo', 'title': 'Select a project'},
      'evidence': const [],
      'review': const {},
    };
  }

  @override
  Future<Map<String, dynamic>> loadRequirementTrace(Uri baseUri, String requirementId) async {
    return {
      'requirement': {'id': requirementId, 'project_id': 'demo', 'title': 'Select a project'},
      'evidence': const [],
      'links': const {},
      'verification_ready': 'candidate',
      'gaps': const ['no_test_evidence'],
    };
  }

  @override
  Future<Map<String, dynamic>> loadRequirementGaps(Uri baseUri, {List<String>? projectIds}) async {
    return {'count': 1, 'items': [{'requirement_id': 'req-1', 'gaps': ['no_test_evidence']}]};
  }

  @override
  Future<Map<String, dynamic>> loadRequirementVerificationReadiness(Uri baseUri, {List<String>? projectIds}) async {
    return {'count': 0, 'items': const []};
  }

  @override
  Future<Map<String, dynamic>> loadRequirementArchitectureGaps(Uri baseUri, {List<String>? projectIds}) async {
    return {'count': 0, 'items': const []};
  }

  @override
  Future<Map<String, dynamic>> loadRequirementUnimplemented(Uri baseUri, {List<String>? projectIds}) async {
    return {'count': 0, 'items': const []};
  }

  @override
  Future<Map<String, dynamic>> loadRequirementUntested(Uri baseUri, {List<String>? projectIds}) async {
    return {'count': 1, 'items': [{'requirement_id': 'req-1'}]};
  }

  @override
  Future<Map<String, dynamic>> loadRequirementHistory(Uri baseUri, {List<String>? projectIds}) async {
    return {'count': 1, 'items': [{'id': 'req-1', 'review_state': 'confirmed'}]};
  }

  @override
  Future<Map<String, dynamic>> confirmRequirement(Uri baseUri, String requirementId, {String operator = 'operator', String notes = ''}) async {
    return {'requirement_id': requirementId, 'status': 'confirmed'};
  }

  @override
  Future<Map<String, dynamic>> rejectRequirement(Uri baseUri, String requirementId, {String operator = 'operator', String notes = ''}) async {
    return {'requirement_id': requirementId, 'status': 'rejected'};
  }

  @override
  Future<Map<String, dynamic>> deferRequirement(Uri baseUri, String requirementId, {String operator = 'operator', String notes = ''}) async {
    return {'requirement_id': requirementId, 'status': 'deferred'};
  }

  @override
  Future<Map<String, dynamic>> loadDecisionInbox(Uri baseUri, {List<String>? projectIds}) async {
    return {
      'count': 1,
      'items': [
        {
          'question': {
            'id': 'decision-q-1',
            'title': 'What should we do next?',
            'description': 'Evaluate the portfolio evidence.',
            'status': 'review_pending',
          },
          'recommendation': {
            'recommended_option': 'address_now',
            'strength': 'strong',
          },
          'review': const {},
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> evaluateDecision(Uri baseUri, Map<String, dynamic> payload) async {
    return {
      'question': {
        'id': 'decision-q-2',
        'title': payload['title'] ?? 'What should we do next?',
        'description': payload['description'] ?? '',
        'status': 'review_pending',
      },
      'criteria': const ['risk', 'reuse'],
      'options': const [],
      'evidence': const [],
      'assessments': const [],
      'recommendation': {
        'id': 'decision-rec-1',
        'question_id': 'decision-q-2',
        'recommended_option': 'address_now',
        'strength': 'strong',
        'summary': 'Focus on the highest-attention evidence.',
      },
      'profile': const {'project_count': 1},
    };
  }

  @override
  Future<Map<String, dynamic>> compareDecisionOptions(Uri baseUri, Map<String, dynamic> payload) async {
    return {
      'question': {
        'id': 'decision-q-3',
        'title': payload['question'] ?? 'Compare options',
        'description': '',
        'status': 'review_pending',
      },
      'criteria': const ['architecture'],
      'options': payload['options'] ?? const [],
      'assessments': const [],
      'recommendation': {
        'id': 'decision-rec-2',
        'question_id': 'decision-q-3',
        'recommended_option': 'Option A',
        'strength': 'moderate',
        'summary': 'Option A is the safest fit.',
      },
    };
  }

  @override
  Future<Map<String, dynamic>> loadDecisionNextActions(Uri baseUri, {List<String>? projectIds}) async {
    return {
      'question': 'What should I work on next?',
      'scope': projectIds ?? const ['demo'],
      'items': [
        {'what': 'address_now', 'urgency': 'strong', 'score': 4.0},
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> loadDecisionReleaseReadiness(Uri baseUri, String projectId) async {
    return {
      'project_id': projectId,
      'status': 'READY',
      'blocking_criteria': const [],
      'passed_criteria': const ['tests'],
      'warnings': const [],
      'unknowns': const [],
      'evidence': const [],
      'recommendation': {'recommended_option': 'READY'},
    };
  }

  @override
  Future<Map<String, dynamic>> loadDecisionReuse(Uri baseUri, {List<String>? projectIds}) async {
    return {
      'status': 'REUSE_NOW',
      'candidates': [
        {'candidate_id': 'reuse-1', 'reason': 'Shared helper is stable.'},
      ],
      'recommendation': {'recommended_option': 'REUSE_NOW'},
    };
  }

  @override
  Future<Map<String, dynamic>> loadDecisionTestPriorities(Uri baseUri, {List<String>? projectIds}) async {
    return {'question': 'Test priority review', 'items': const []};
  }

  @override
  Future<Map<String, dynamic>> loadDecisionDebtPriorities(Uri baseUri, {List<String>? projectIds}) async {
    return {'question': 'Technical debt review', 'items': const []};
  }

  @override
  Future<Map<String, dynamic>> runDecisionScenario(Uri baseUri, Map<String, dynamic> scenario, {List<String>? projectIds}) async {
    return {
      'scenario': scenario,
      'expected_affected_areas': const [],
      'known_required_changes': const [],
      'possible_impacts': const [],
      'unknown_impacts': const [],
      'evidence_gaps': const [],
    };
  }

  @override
  Future<Map<String, dynamic>> loadDecisionHistory(Uri baseUri, {List<String>? projectIds}) async {
    return {
      'count': 1,
      'items': [
        {
          'question': {'id': 'decision-q-1', 'title': 'What should we do next?', 'status': 'accepted'},
          'recommendation': {'recommended_option': 'address_now'},
          'review': {'review_state': 'accepted'},
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> acceptDecision(Uri baseUri, String questionId, {String operator = 'operator', String selectedOption = '', String notes = ''}) async {
    return {'question_id': questionId, 'status': 'accepted'};
  }

  @override
  Future<Map<String, dynamic>> rejectDecision(Uri baseUri, String questionId, {String operator = 'operator', String selectedOption = '', String notes = ''}) async {
    return {'question_id': questionId, 'status': 'rejected'};
  }

  @override
  Future<Map<String, dynamic>> deferDecision(Uri baseUri, String questionId, {String operator = 'operator', String selectedOption = '', String notes = ''}) async {
    return {'question_id': questionId, 'status': 'deferred'};
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
    expect(find.text('Requirements Intelligence'), findsOneWidget);
  });
}
