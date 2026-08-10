import 'package:desktop/app.dart';
import 'package:desktop/neos_client.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeNeosClient implements NeosClient {
  Map<String, dynamic> _workspacePayload(String projectId) {
    return {
      'schema_version': 1,
      'project_id': projectId,
      'identity': {
        'project_id': projectId,
        'name': 'Demo Project',
        'repo_path': 'C:/demo',
        'manifest_path': 'C:/demo/project.json',
      },
      'project': {
        'project_id': projectId,
        'name': 'Demo Project',
      },
      'summary': {
        'project_id': projectId,
        'name': 'Demo Project',
        'classification': 'FIRST_PARTY_ACTIVE',
        'integration_mode': 'CONTRACTED',
        'readiness': 'READY',
        'freshness': 'FRESH',
        'contract_state': 'present',
        'project_registered': true,
        'scan_present': true,
        'manifest_present': true,
        'needs_attention': false,
      },
      'classification': {
        'project_id': projectId,
        'classification': 'FIRST_PARTY_ACTIVE',
        'is_first_party': true,
        'reason': 'registered-project, scan-present',
        'signals': const ['registered-project', 'scan-present'],
      },
      'integration': {
        'mode': 'CONTRACTED',
        'readiness': 'READY',
        'release_readiness': {'status': 'READY'},
        'contract_state': 'present',
      },
      'contract': {
        'adapter_state': 'connected',
        'contract_state': 'present',
        'project_contract': {'contract_type': 'PROJECT_CONTRACT'},
        'capabilities_contract': const {},
        'dependencies_contract': const {},
        'safety_boundary_contract': const {},
        'release_state_contract': const {},
        'registry_contracts': const {},
        'contract_sources': const [],
      },
      'repository': {
        'project_id': projectId,
        'declared_path': 'C:/demo',
        'observed_path': 'C:/demo',
        'exists': true,
        'git': {'repo_path': 'C:/demo', 'branch': 'main', 'commit': 'abc123', 'dirty': false},
        'manifest_status': 'present',
        'manifest_path': 'C:/demo/project.json',
        'scan_id': 'scan-1',
      },
      'dependencies': {
        'declared': const [],
        'observed': const [],
        'reconciled': {
          'status': 'NOT_APPLICABLE',
          'count': 0,
          'items': const [],
          'summary': {'declared_count': 0, 'observed_count': 0, 'shared_count': 0},
        },
      },
      'requirements': {'count': 1, 'items': [{'id': 'req-1', 'title': 'Select a project'}]},
      'decisions': {'count': 1, 'items': ['decision-1']},
      'memory': {'project_id': projectId, 'summary': {'decisions': 1}},
      'flight': {'project_id': projectId, 'status': 'available'},
      'hardware': {
        'project_id': projectId,
        'summary': {'board_count': 1, 'component_count': 2, 'pin_mapping_count': 2},
      },
      'firmware': {
        'project_id': projectId,
        'summary': {'environment_count': 1, 'target_count': 1, 'task_count': 1},
      },
      'release': {'project_id': projectId, 'status': 'READY'},
      'safety': {
        'project_id': projectId,
        'boundary': const {},
        'summary': {
          'local_only_operation': true,
          'cloud_allowed': false,
          'device_flashing_allowed': false,
          'actuator_authority': false,
          'operator_approval_required': true,
        },
      },
      'evidence': {
        'project_registered': true,
        'scan_present': true,
        'manifest_present': true,
        'contract_sources_count': 1,
        'genome_present': true,
        'memory_present': true,
        'flight_present': true,
        'hardware_present': true,
        'firmware_present': true,
        'readiness': 'READY',
      },
      'drift': {'status': 'aligned'},
      'impact': {'count': 0, 'items': const []},
      'freshness': {'status': 'FRESH', 'reason': 'current_git_state_matches_latest_scan'},
      'provenance': {
        'declared_sources': const ['C:/demo/project.json'],
        'observed_sources': [
          {'kind': 'git', 'repo_path': 'C:/demo', 'commit': 'abc123', 'branch': 'main'},
          {'kind': 'scan', 'scan_id': 'scan-1', 'created_at': '2026-08-07T00:00:00Z'},
        ],
        'contract_sources': const [],
        'analysis_sources': const ['project_registry_v2', 'architecture_registry', 'release_readiness'],
      },
      'attention': const [],
    };
  }

  @override
  Future<ServiceHealthInfo> probeHealth(Uri baseUri) async {
    return ServiceHealthInfo.fromJson({
      'status': 'healthy',
      'service_name': 'NEOS Local Service',
      'service_version': '1.3.0',
      'api_version': 'v1',
      'schema_version': 11,
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
      'workspace': _workspacePayload(projectId),
      'summary': {
        'name': 'Demo Project',
        'status': 'healthy',
      },
      'genome': {'project_id': projectId, 'maturity': {'status': 'stable'}},
      'memory': {'project_id': projectId, 'summary': {'decisions': 1}},
      'flight': {'project_id': projectId, 'status': 'available'},
      'hardware': {
        'project_id': projectId,
        'summary': {
          'board_count': 1,
          'component_count': 2,
          'pin_mapping_count': 2,
          'validation_state': 'validated',
          'gap_count': 1,
        },
        'boards': [
          {
            'id': 'board-1',
            'name': 'Demo Board',
            'revision': 'A',
          },
        ],
        'components': [
          {'id': 'component-1', 'description': 'MCU'},
        ],
        'pins': [
          {'hardware_pin': 'GPIO21', 'signal': 'I2C_SDA'},
        ],
        'validations': [
          {'validation_type': 'bench test', 'result': 'pass'},
        ],
        'risks': const [],
        'gaps': const [],
      },
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
        'schema': {'database_schema': 11},
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
  Future<Map<String, dynamic>> loadWorkspace(Uri baseUri, {List<String>? projectIds, bool includeNonFirstParty = false}) async {
    return {
      'schema_version': 1,
      'project_count': 1,
      'items': [_workspacePayload('demo')['summary']],
    };
  }

  @override
  Future<Map<String, dynamic>> loadWorkspaceProject(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId);

  @override
  Future<Map<String, dynamic>> loadWorkspaceSummary(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['summary'] as Map<String, dynamic>;

  @override
  Future<Map<String, dynamic>> loadWorkspaceClassification(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['classification'] as Map<String, dynamic>;

  @override
  Future<Map<String, dynamic>> loadWorkspaceIntegration(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['integration'] as Map<String, dynamic>;

  @override
  Future<Map<String, dynamic>> loadWorkspaceContracts(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['contract'] as Map<String, dynamic>;

  @override
  Future<Map<String, dynamic>> loadWorkspaceDependencies(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['dependencies'] as Map<String, dynamic>;

  @override
  Future<Map<String, dynamic>> loadWorkspaceFreshness(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['freshness'] as Map<String, dynamic>;

  @override
  Future<Map<String, dynamic>> loadWorkspaceProvenance(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['provenance'] as Map<String, dynamic>;

  @override
  Future<Map<String, dynamic>> loadWorkspaceSafety(Uri baseUri, String projectId, {String? repoPath}) async => _workspacePayload(projectId)['safety'] as Map<String, dynamic>;

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
  Future<Map<String, dynamic>> loadHardware(Uri baseUri, String projectId) async {
    return {
      'project_id': projectId,
      'summary': {
        'board_count': 1,
        'component_count': 2,
        'pin_mapping_count': 2,
        'validation_state': 'validated',
        'gap_count': 1,
      },
      'boards': [
        {'id': 'board-1', 'name': 'Demo Board', 'revision': 'A'},
      ],
      'components': [
        {'id': 'component-1', 'description': 'MCU'},
      ],
      'pins': [
        {'hardware_pin': 'GPIO21', 'signal': 'I2C_SDA'},
      ],
      'validations': [
        {'validation_type': 'bench test', 'result': 'pass'},
      ],
      'risks': const [],
      'gaps': const [],
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
  Future<Map<String, dynamic>> loadToday(Uri baseUri, {List<String>? projectIds}) async {
    return {
      'generated_at': '2026-08-08T00:00:00Z',
      'selected_project_id': 'demo',
      'projects': [
        {
          'project_id': 'demo',
          'name': 'Demo Project',
          'status': 'healthy',
          'scan_freshness': 'fresh',
          'work_item_count': 1,
        },
      ],
      'work_queue': {
        'count': 1,
        'summary': {'open_count': 1, 'high_priority_count': 1, 'project_count': 1},
        'items': [
          {
            'id': 'work-1',
            'project_id': 'demo',
            'scope': 'project',
            'category': 'requirements',
            'priority': 'high',
            'title': 'Close requirement gap',
            'why': 'Demo work item',
            'evidence_json': '{}',
            'recommended_action': 'Review the gap',
            'status': 'open',
            'source': 'command-centre',
            'source_fingerprint': 'work-1',
            'created_at': '2026-08-08T00:00:00Z',
            'updated_at': '2026-08-08T00:00:00Z',
            'metadata_json': '{}',
          },
        ],
      },
      'highlights': [
        {'title': 'Close requirement gap', 'why': 'Demo work item'},
      ],
      'command_centre_health': {
        'status': 'healthy',
        'project_count': 1,
        'open_work_items': 1,
        'active_refresh_jobs': 0,
        'session_count': 1,
        'last_refresh_job': null,
      },
    };
  }

  @override
  Future<Map<String, dynamic>> loadWorkQueue(Uri baseUri, {List<String>? projectIds, bool includeClosed = false}) async {
    final today = await loadToday(baseUri, projectIds: projectIds);
    return {
      'generated_at': '2026-08-08T00:00:00Z',
      'project_ids': projectIds ?? ['demo'],
      'count': 1,
      'summary': {'open_count': 1, 'high_priority_count': 1, 'project_count': 1},
      'items': today['work_queue']['items'],
    };
  }

  @override
  Future<Map<String, dynamic>> loadWorkItem(Uri baseUri, String workItemId) async {
    return {'id': workItemId, 'project_id': 'demo', 'status': 'open'};
  }

  @override
  Future<Map<String, dynamic>> acknowledgeWorkItem(Uri baseUri, String workItemId, {String operator = 'operator', String notes = ''}) async {
    return {'id': workItemId, 'status': 'acknowledged'};
  }

  @override
  Future<Map<String, dynamic>> deferWorkItem(Uri baseUri, String workItemId, {String operator = 'operator', String notes = ''}) async {
    return {'id': workItemId, 'status': 'deferred'};
  }

  @override
  Future<Map<String, dynamic>> dismissWorkItem(Uri baseUri, String workItemId, {String operator = 'operator', String notes = ''}) async {
    return {'id': workItemId, 'status': 'dismissed'};
  }

  @override
  Future<Map<String, dynamic>> resolveWorkItem(Uri baseUri, String workItemId, {String operator = 'operator', String notes = ''}) async {
    return {'id': workItemId, 'status': 'done'};
  }

  @override
  Future<Map<String, dynamic>> refreshProjectIntelligence(Uri baseUri, String projectId, {Map<String, dynamic>? options}) async {
    return {'job_id': 'job-1', 'project_id': projectId, 'status': 'completed', 'outputs': const {}};
  }

  @override
  Future<Map<String, dynamic>> loadRefreshJob(Uri baseUri, String jobId) async {
    return {'job_id': jobId, 'project_id': 'demo', 'status': 'completed'};
  }

  @override
  Future<Map<String, dynamic>> loadAppSession(Uri baseUri, {String sessionKey = 'workspace'}) async {
    return {'session_key': sessionKey, 'state': {'selected_project_id': 'demo'}, 'updated_at': '2026-08-08T00:00:00Z'};
  }

  @override
  Future<Map<String, dynamic>> saveAppSession(Uri baseUri, Map<String, dynamic> state, {String sessionKey = 'workspace'}) async {
    return {'session_key': sessionKey, 'state': state, 'updated_at': '2026-08-08T00:00:00Z'};
  }

  @override
  Future<Map<String, dynamic>> searchCommandCentre(Uri baseUri, String query, {List<String>? projectIds, int limit = 20}) async {
    return {
      'query': query,
      'count': 1,
      'items': [
        {'kind': 'work_item', 'project_id': 'demo', 'title': 'Close requirement gap', 'snippet': 'Demo work item', 'source': 'work_items', 'score': 10},
      ],
    };
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

    expect(find.text('NEOS Command Centre'), findsOneWidget);
    expect(find.text('Today'), findsWidgets);
    expect(find.text('Work Queue'), findsOneWidget);
    expect(find.text('Demo Project'), findsWidgets);
    expect(find.text('Navigation'), findsOneWidget);
    expect(find.text('AI Partner'), findsOneWidget);
    expect(find.text('Hardware Centre'), findsOneWidget);
  });
}
