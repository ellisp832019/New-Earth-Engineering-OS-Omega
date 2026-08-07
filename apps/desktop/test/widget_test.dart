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
      'service_version': '0.1.0',
      'api_version': 'v1',
      'schema_version': 6,
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
        'schema': {'database_schema': 6},
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
