import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';

import 'neos_client.dart';
import 'portfolio_workspace.dart';

Map<String, dynamic> _asMap(dynamic value) {
  if (value is Map<String, dynamic>) {
    return value;
  }
  if (value is Map) {
    return value.map((key, item) => MapEntry(key.toString(), item));
  }
  return <String, dynamic>{};
}

List<dynamic> _asList(dynamic value) {
  if (value is List) {
    return value;
  }
  return const <dynamic>[];
}

String _asString(dynamic value, [String fallback = '']) {
  return value == null ? fallback : value.toString();
}

int _asInt(dynamic value, [int fallback = 0]) {
  if (value is int) {
    return value;
  }
  return int.tryParse(_asString(value)) ?? fallback;
}

bool _asBool(dynamic value, [bool fallback = false]) {
  if (value is bool) {
    return value;
  }
  return fallback;
}

enum _Destination {
  home,
  projects,
  portfolio,
  intelligence,
  graph,
  features,
  tests,
  releases,
  timeline,
  documentation,
  assistant,
  plugins,
  health,
  settings,
}

class _NavItem {
  const _NavItem(this.destination, this.icon, this.label);

  final _Destination destination;
  final IconData icon;
  final String label;
}

class NeosApp extends StatelessWidget {
  const NeosApp({super.key, required this.client});

  final NeosClient client;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NEOS Windows Desktop',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0F766E),
          surface: const Color(0xFFF8FAFC),
        ),
        scaffoldBackgroundColor: const Color(0xFFF1F5F9),
      ),
      home: NeosShell(client: client),
    );
  }
}

class NeosShell extends StatefulWidget {
  const NeosShell({
    super.key,
    required this.client,
    this.initialServiceUrl = 'http://127.0.0.1:8765',
  });

  final NeosClient client;
  final String initialServiceUrl;

  @override
  State<NeosShell> createState() => _NeosShellState();
}

class _NeosShellState extends State<NeosShell> {
  final TextEditingController _serviceController = TextEditingController();
  final TextEditingController _projectFilterController = TextEditingController();
  final TextEditingController _assistantQuestionController = TextEditingController(text: 'What should I work on next?');
  final TextEditingController _aiProviderController = TextEditingController();
  final TextEditingController _aiModelController = TextEditingController();
  final TextEditingController _aiEndpointController = TextEditingController();
  final TextEditingController _aiTimeoutController = TextEditingController();
  final TextEditingController _aiContextBudgetController = TextEditingController();
  final TextEditingController _aiMaxOutputController = TextEditingController();

  _Destination _destination = _Destination.home;
  ServiceOverview? _overview;
  ProjectRecord? _project;
  String? _selectedProjectId;
  String? _error;
  bool _loadingOverview = true;
  bool _loadingProject = false;
  bool _loadingAi = false;
  bool _savingAiSettings = false;
  bool _askingAi = false;
  String? _aiError;
  String? _selectedConversationId;
  String _assistantMode = 'ask';
  List<AIProviderSummary> _aiProviders = const [];
  List<AIConversationSummary> _aiConversations = const [];
  Map<String, dynamic>? _aiSettings;
  Map<String, dynamic>? _aiProviderHealth;
  Map<String, dynamic>? _aiResponse;
  List<Map<String, dynamic>> _aiCitations = const [];

  static const List<_NavItem> _items = <_NavItem>[
    _NavItem(_Destination.home, Icons.home_outlined, 'Home'),
    _NavItem(_Destination.projects, Icons.folder_outlined, 'Projects'),
    _NavItem(_Destination.portfolio, Icons.account_tree_outlined, 'Portfolio Workspace'),
    _NavItem(_Destination.intelligence, Icons.schema_outlined, 'Repository Intelligence'),
    _NavItem(_Destination.graph, Icons.graphic_eq_outlined, 'Knowledge Graph'),
    _NavItem(_Destination.features, Icons.label_outline, 'Features & Requirements'),
    _NavItem(_Destination.tests, Icons.fact_check_outlined, 'Tests & Evidence'),
    _NavItem(_Destination.releases, Icons.rocket_launch_outlined, 'Releases'),
    _NavItem(_Destination.timeline, Icons.timeline_outlined, 'Timeline'),
    _NavItem(_Destination.documentation, Icons.menu_book_outlined, 'Documentation'),
    _NavItem(_Destination.assistant, Icons.psychology_outlined, 'AI Assistant'),
    _NavItem(_Destination.plugins, Icons.extension_outlined, 'Plugins'),
    _NavItem(_Destination.health, Icons.health_and_safety_outlined, 'System Health'),
    _NavItem(_Destination.settings, Icons.settings_outlined, 'Settings'),
  ];

  Uri get _serviceUri {
    final text = _serviceController.text.trim();
    return Uri.parse(text.isEmpty ? widget.initialServiceUrl : text);
  }

  @override
  void initState() {
    super.initState();
    _serviceController.text = widget.initialServiceUrl;
    _refreshOverview(selectFirstProject: true);
  }

  @override
  void dispose() {
    _serviceController.dispose();
    _projectFilterController.dispose();
    _assistantQuestionController.dispose();
    _aiProviderController.dispose();
    _aiModelController.dispose();
    _aiEndpointController.dispose();
    _aiTimeoutController.dispose();
    _aiContextBudgetController.dispose();
    _aiMaxOutputController.dispose();
    super.dispose();
  }

  Future<void> _refreshOverview({required bool selectFirstProject}) async {
    setState(() {
      _loadingOverview = true;
      _error = null;
    });
    try {
      final overview = await widget.client.loadOverview(_serviceUri);
      final nextProjectId = selectFirstProject
          ? (overview.projects.isEmpty ? null : overview.projects.first.projectId)
          : _selectedProjectId;
      setState(() {
        _overview = overview;
        _loadingOverview = false;
      });
      if (nextProjectId != null) {
        await _loadProject(nextProjectId);
      } else {
        setState(() {
          _project = null;
          _selectedProjectId = null;
          _loadingProject = false;
        });
      }
    } catch (error) {
      setState(() {
        _overview = null;
        _project = null;
        _loadingOverview = false;
        _loadingProject = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _loadProject(String projectId) async {
    setState(() {
      _loadingProject = true;
      _selectedProjectId = projectId;
      _error = null;
    });
    try {
      final project = await widget.client.loadProject(_serviceUri, projectId);
      setState(() {
        _project = project;
        _loadingProject = false;
      });
    } catch (error) {
      setState(() {
        _project = null;
        _loadingProject = false;
        _error = error.toString();
      });
    }
  }

  void _selectDestination(_Destination destination) {
    setState(() {
      _destination = destination;
    });
    if (destination == _Destination.assistant || destination == _Destination.settings || destination == _Destination.health) {
      unawaited(_refreshAiWorkspace());
    }
  }

  Future<void> _refreshAiWorkspace() async {
    setState(() {
      _loadingAi = true;
      _aiError = null;
    });
    try {
      final results = await Future.wait([
        widget.client.loadAiSettings(_serviceUri),
        widget.client.loadAiProviders(_serviceUri),
        widget.client.loadAiConversations(_serviceUri, projectId: _selectedProjectId),
      ]);
      final settings = results[0] as Map<String, dynamic>;
      final providers = results[1] as List<AIProviderSummary>;
      final conversations = results[2] as List<AIConversationSummary>;
      final providerHealth = _asMap(settings['provider_health']);
      final config = _asMap(settings['settings']);
      Map<String, dynamic>? conversation;
      if (_selectedConversationId != null) {
        try {
          conversation = await widget.client.loadAiConversation(_serviceUri, _selectedConversationId!);
        } catch (_) {
          conversation = null;
        }
      }
      setState(() {
        _aiSettings = settings;
        _aiProviders = providers;
        _aiConversations = conversations;
        _aiProviderHealth = providerHealth;
        _aiResponse = conversation == null || _asList(conversation['turns']).isEmpty
            ? _aiResponse
            : _asMap(_asList(conversation['turns']).last)['response_json'] is Map<String, dynamic>
                ? _asMap(_asList(conversation['turns']).last)['response_json'] as Map<String, dynamic>
                : _aiResponse;
        _loadingAi = false;
      });
      _aiProviderController.text = _asString(config['provider_id'], 'mock');
      _aiModelController.text = _asString(config['model'], 'mock-engineer-v1');
      _aiEndpointController.text = _asString(config['endpoint']);
      _aiTimeoutController.text = _asInt(config['timeout_seconds'], 30).toString();
      _aiContextBudgetController.text = _asInt(config['context_budget'], 24).toString();
      _aiMaxOutputController.text = _asInt(config['max_output_tokens'], 1200).toString();
    } catch (error) {
      setState(() {
        _loadingAi = false;
        _aiError = error.toString();
      });
    }
  }

  Future<void> _loadAiConversation(String conversationId) async {
    setState(() {
      _selectedConversationId = conversationId;
      _aiError = null;
    });
    try {
      final conversation = await widget.client.loadAiConversation(_serviceUri, conversationId);
      final turns = _asList(conversation['turns']).cast<dynamic>();
      Map<String, dynamic>? response;
      List<Map<String, dynamic>> citations = const [];
      if (turns.isNotEmpty) {
        final lastTurn = _asMap(turns.last);
        response = _asMap(lastTurn['response_json']);
        final requestId = _asString(lastTurn['request_id']);
        if (requestId.isNotEmpty) {
          final citationPayload = await widget.client.loadAiRequestCitations(_serviceUri, requestId);
          citations = _asList(citationPayload['citations']).map((item) => _asMap(item)).toList(growable: false);
        }
      }
      setState(() {
        _aiResponse = response;
        _aiCitations = citations;
      });
    } catch (error) {
      setState(() {
        _aiError = error.toString();
      });
    }
  }

  Future<void> _submitAiQuestion() async {
    final projectId = _selectedProjectId;
    final question = _assistantQuestionController.text.trim();
    if (projectId == null || projectId.isEmpty) {
      setState(() {
        _aiError = 'Select a project before asking a question.';
      });
      return;
    }
    if (question.isEmpty) {
      setState(() {
        _aiError = 'Enter an engineering question first.';
      });
      return;
    }
    setState(() {
      _askingAi = true;
      _aiError = null;
    });
    try {
      final response = await widget.client.askAi(
        _serviceUri,
        projectId: projectId,
        question: question,
        conversationId: _selectedConversationId,
        mode: _assistantMode,
      );
      final conversationId = _asString(response['conversation_id']);
      final requestId = _asString(response['request_id']);
      final citationsPayload = requestId.isNotEmpty
          ? await widget.client.loadAiRequestCitations(_serviceUri, requestId)
          : <String, dynamic>{'citations': const []};
      final citations = _asList(citationsPayload['citations']).map((item) => _asMap(item)).toList(growable: false);
      setState(() {
        _aiResponse = response;
        _aiCitations = citations;
        _selectedConversationId = conversationId.isEmpty ? _selectedConversationId : conversationId;
        _askingAi = false;
      });
      await _refreshAiWorkspace();
      if (_selectedConversationId != null && _selectedConversationId!.isNotEmpty) {
        await _loadAiConversation(_selectedConversationId!);
      }
    } catch (error) {
      setState(() {
        _askingAi = false;
        _aiError = error.toString();
      });
    }
  }

  Future<void> _saveAiSettings() async {
    setState(() {
      _savingAiSettings = true;
      _aiError = null;
    });
    try {
      final payload = <String, dynamic>{
        'provider_id': _aiProviderController.text.trim(),
        'model': _aiModelController.text.trim(),
        'endpoint': _aiEndpointController.text.trim(),
        'timeout_seconds': int.tryParse(_aiTimeoutController.text.trim()) ?? 30,
        'context_budget': int.tryParse(_aiContextBudgetController.text.trim()) ?? 24,
        'max_output_tokens': int.tryParse(_aiMaxOutputController.text.trim()) ?? 1200,
        'streaming': _asBool(_asMap(_aiSettings?['settings'])['streaming']),
      };
      final updated = await widget.client.saveAiSettings(_serviceUri, payload);
      setState(() {
        _aiSettings = updated;
        _savingAiSettings = false;
      });
      await _refreshAiWorkspace();
    } catch (error) {
      setState(() {
        _savingAiSettings = false;
        _aiError = error.toString();
      });
    }
  }

  String _prettyJson(dynamic data) {
    if (data == null) {
      return 'No data available.';
    }
    try {
      return const JsonEncoder.withIndent('  ').convert(data);
    } catch (_) {
      return data.toString();
    }
  }

  int _countOf(dynamic value) {
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

  ProjectOverview? _selectedOverview() {
    final selectedId = _selectedProjectId;
    if (selectedId == null) {
      return null;
    }
    for (final project in _overview?.projects ?? const <ProjectOverview>[]) {
      if (project.projectId == selectedId) {
        return project;
      }
    }
    return null;
  }

  List<ProjectOverview> get _filteredProjects {
    final projects = _overview?.projects ?? const <ProjectOverview>[];
    final filter = _projectFilterController.text.trim().toLowerCase();
    if (filter.isEmpty) {
      return projects;
    }
    return projects.where((project) {
      return project.projectId.toLowerCase().contains(filter) ||
          project.name.toLowerCase().contains(filter) ||
          project.repoPath.toLowerCase().contains(filter);
    }).toList(growable: false);
  }

  Widget _chip(String label, {Color? backgroundColor}) {
    return Chip(
      label: Text(label),
      backgroundColor: backgroundColor ?? const Color(0xFFE0F2F1),
      side: BorderSide.none,
      labelStyle: const TextStyle(color: Color(0xFF134E4A)),
    );
  }

  Widget _metricCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
  }) {
    return Card(
      elevation: 0,
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: const Color(0xFF0F766E)),
            const SizedBox(height: 14),
            Text(title, style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 6),
            Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.black54)),
          ],
        ),
      ),
    );
  }

  Widget _panel({
    required String title,
    String? subtitle,
    Widget? trailing,
    required Widget child,
  }) {
    return Card(
      elevation: 0,
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                      if (subtitle != null) ...[
                        const SizedBox(height: 4),
                        Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.black54)),
                      ],
                    ],
                  ),
                ),
                ...?(trailing == null ? null : [trailing]),
              ],
            ),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }

  Widget _jsonPanel(String title, dynamic data, {String? subtitle}) {
    return _panel(
      title: title,
      subtitle: subtitle,
      child: Container(
        constraints: const BoxConstraints(maxHeight: 320),
        width: double.infinity,
        decoration: BoxDecoration(
          color: const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(12),
          child: SelectableText(
            _prettyJson(data),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(fontFamily: 'Consolas'),
          ),
        ),
      ),
    );
  }

  Widget _navigationPane() {
    return Container(
      width: 320,
      decoration: const BoxDecoration(
        color: Color(0xFFF8FAFC),
        border: Border(right: BorderSide(color: Color(0xFFE2E8F0))),
      ),
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 4, 8, 12),
            child: Text('Navigation', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          ),
          for (final item in _items)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                selected: _destination == item.destination,
                selectedTileColor: const Color(0xFFD9F0EE),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                leading: Icon(item.icon, color: _destination == item.destination ? const Color(0xFF0F766E) : Colors.black54),
                title: Text(item.label),
                onTap: () => _selectDestination(item.destination),
              ),
            ),
        ],
      ),
    );
  }

  Widget _homeView() {
    final overview = _overview;
    final project = _project;
    if (_loadingOverview && overview == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Home',
            subtitle: 'Project health, latest scan activity, and next actions from the local NEOS service.',
            trailing: IconButton(
              onPressed: () => _refreshOverview(selectFirstProject: false),
              icon: const Icon(Icons.refresh),
            ),
            child: Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _metricCard(
                  title: 'Service',
                  value: overview?.status ?? 'offline',
                  subtitle: overview == null ? 'Cannot reach the local service' : '${overview.serviceName} / ${overview.apiVersion}',
                  icon: Icons.dns_outlined,
                ),
                _metricCard(
                  title: 'Projects',
                  value: (overview?.projects.length ?? 0).toString(),
                  subtitle: 'Registered in the local database',
                  icon: Icons.folder_copy_outlined,
                ),
                _metricCard(
                  title: 'Selected project',
                  value: project?.projectId ?? 'none',
                  subtitle: project?.summary['name']?.toString() ?? 'Choose a project from the sidebar',
                  icon: Icons.hub_outlined,
                ),
                _metricCard(
                  title: 'Database',
                  value: overview == null ? 'n/a' : '${(overview.databaseSizeBytes / 1024).round()} KB',
                  subtitle: overview?.dbPath ?? 'Local SQLite store',
                  icon: Icons.storage_outlined,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          LayoutBuilder(
            builder: (context, constraints) {
              final split = constraints.maxWidth > 1100;
              final actions = _panel(
                title: 'Recommended next actions',
                subtitle: 'Thin-client reminders based on what the local service can currently see.',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    _Bullet(text: 'Refresh after a scan or build to keep the desktop view current.'),
                    _Bullet(text: 'Switch projects to compare genome, memory, and flight evidence side by side.'),
                    _Bullet(text: 'Use the JSON panes when you need the exact backend payload for a handoff or review.'),
                    _Bullet(text: 'Keep the Python service on localhost; the desktop shell does not own project truth.'),
                  ],
                ),
              );
              final latestScan = _jsonPanel('Latest scan', overview?.lastScan, subtitle: 'Most recent scan row reported by the service.');
              if (split) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: actions),
                    const SizedBox(width: 16),
                    Expanded(child: latestScan),
                  ],
                );
              }
              return Column(
                children: [
                  actions,
                  const SizedBox(height: 16),
                  latestScan,
                ],
              );
            },
          ),
          const SizedBox(height: 16),
          if (overview != null)
            _panel(
              title: 'Project inventory',
              subtitle: 'Registered projects from the NEOS service.',
              child: Column(
                children: overview.projects
                    .take(5)
                    .map(
                      (item) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        onTap: () => _loadProject(item.projectId),
                        leading: const Icon(Icons.folder_outlined),
                        title: Text(item.name),
                        subtitle: Text(item.repoPath),
                        trailing: Text(item.genomeStatus),
                      ),
                    )
                    .toList(growable: false),
              ),
            ),
        ],
      ),
    );
  }

  Widget _projectsView() {
    final projects = _filteredProjects;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Projects',
            subtitle: 'Browse registered repositories and inspect the currently selected project.',
            trailing: SizedBox(
              width: 280,
              child: TextField(
                controller: _projectFilterController,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search),
                  hintText: 'Filter projects',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
            ),
            child: projects.isEmpty
                ? const Text('No projects are available yet.')
                : Column(
                    children: [
                      for (final project in projects)
                        Card(
                          elevation: 0,
                          color: _selectedProjectId == project.projectId ? const Color(0xFFE0F2F1) : const Color(0xFFF8FAFC),
                          child: ListTile(
                            onTap: () => _loadProject(project.projectId),
                            title: Text(project.name),
                            subtitle: Text('${project.repoPath}\nBranch: ${project.branch}'),
                            isThreeLine: true,
                            trailing: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(project.projectId),
                                Text(project.scanFreshness, style: Theme.of(context).textTheme.bodySmall),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
          ),
          const SizedBox(height: 16),
          _selectedProjectPanel(),
        ],
      ),
    );
  }

  Widget _selectedProjectPanel() {
    final project = _project;
    if (project == null) {
      return _panel(
        title: 'Selected project',
        subtitle: 'No project selected yet.',
        child: const Text('Pick a project from the list to inspect its genome, memory, flight and evidence payloads.'),
      );
    }

    final overview = _selectedOverview();
    return Column(
      children: [
        _panel(
          title: project.projectId,
          subtitle: project.project['name']?.toString() ?? 'Project detail',
          trailing: IconButton(
            onPressed: () => _loadProject(project.projectId),
            icon: const Icon(Icons.refresh),
          ),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (overview != null) _chip('Branch ${overview.branch}'),
              if (overview != null) _chip('Genome ${overview.genomeStatus}'),
              if (overview != null) _chip('Memory ${overview.memoryStatus}'),
              if (overview != null) _chip('Flight ${overview.flightStatus}'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _jsonPanel('Project summary', project.summary),
        const SizedBox(height: 16),
        _jsonPanel('Genome', project.genome, subtitle: 'Latest project genome payload from the backend.'),
        const SizedBox(height: 16),
        _jsonPanel('Memory', project.memory, subtitle: 'Latest engineering memory payload from the backend.'),
        const SizedBox(height: 16),
        _jsonPanel('Flight', project.flight, subtitle: 'Latest flight recorder payload from the backend.'),
      ],
    );
  }

  Widget _projectPayloadView({
    required String title,
    required String subtitle,
    required List<String> keys,
  }) {
    final project = _project;
    if (project == null) {
      return Center(child: Text('Select a project to view $title.', style: Theme.of(context).textTheme.titleMedium));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: title,
            subtitle: subtitle,
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip(project.projectId),
                _chip('Project ${project.projectId}'),
                _chip('Genome ${_countOf(project.genome)}'),
                _chip('Memory ${_countOf(project.memory)}'),
                _chip('Flight ${_countOf(project.flight)}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          for (final key in keys) ...[
            _jsonPanel(key[0].toUpperCase() + key.substring(1), project.section(key), subtitle: 'Backend payload for $key.'),
            const SizedBox(height: 16),
          ],
        ],
      ),
    );
  }

  Widget _graphView() {
    final project = _project;
    if (project == null) {
      return const Center(child: Text('Select a project to inspect relationships.'));
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Knowledge Graph',
            subtitle: 'Dependencies, provenance and reasoning helpers are all sourced from the local service.',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip(project.projectId),
                _chip('Dependencies ${_countOf(project.section('dependencies'))}'),
                _chip('Why ${_countOf(project.section('why'))}'),
                _chip('Trace ${_countOf(project.section('trace'))}'),
                _chip('Impact ${_countOf(project.section('impact'))}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Dependencies', project.section('dependencies'), subtitle: 'Relationship inventory and provenance details.'),
          const SizedBox(height: 16),
          _jsonPanel('Why', project.section('why'), subtitle: 'Why-answer payloads for the selected project.'),
          const SizedBox(height: 16),
          _jsonPanel('Trace', project.section('trace'), subtitle: 'Trace data for the selected project.'),
          const SizedBox(height: 16),
          _jsonPanel('Impact', project.section('impact'), subtitle: 'Impact data for the selected project.'),
        ],
      ),
    );
  }

  Widget _assistantView() {
    final project = _project;
    final response = _aiResponse;
    final providerHealth = _aiProviderHealth ?? const <String, dynamic>{};
    final providerName = _asString(providerHealth['name'], _asString(providerHealth['provider_id'], 'not configured'));
    final providerStatus = _asString(providerHealth['message'], 'Provider not configured');
    final citations = _aiCitations;
    final facts = _asList(response?['facts']).map((item) => _asMap(item)).toList(growable: false);
    final derivedFacts = _asList(response?['derived_facts']).map((item) => _asMap(item)).toList(growable: false);
    final inferences = _asList(response?['inferences']).map((item) => _asMap(item)).toList(growable: false);
    final recommendations = _asList(response?['recommendations']).map((item) => _asMap(item)).toList(growable: false);
    final unknowns = _asList(response?['unknowns']).map((item) => _asMap(item)).toList(growable: false);
    final responseContext = _asMap(response?['context_snapshot']);
    final contextJson = const JsonEncoder.withIndent('  ').convert(responseContext);

    Widget sectionList(String title, List<Map<String, dynamic>> items, String emptyMessage) {
      return _panel(
        title: title,
        subtitle: '${items.length} item(s)',
        child: items.isEmpty
            ? Text(emptyMessage)
            : Column(
                children: [
                  for (final item in items)
                    ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: Text(_asString(item['text'], _asString(item['summary'], _asString(item['excerpt'], 'Item')))),
                      subtitle: Text(
                        _asString(item['basis'], _asString(item['basis'], _asString(item['path'], ''))),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
              ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'AI Engineering Partner',
            subtitle: 'Evidence-grounded questions, bounded context, and citation-first answers.',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                _chip('Project ${project?.projectId ?? 'none'}'),
                _chip('Provider $providerName'),
                _chip(_asString(response?['model'], _aiModelController.text.isEmpty ? 'mock-engineer-v1' : _aiModelController.text)),
                _chip(_asString(response?['status'], providerStatus)),
                if (_loadingAi) const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                if (_aiError != null)
                  Chip(
                    backgroundColor: const Color(0xFFFEE2E2),
                    label: Text(_aiError!, maxLines: 2, overflow: TextOverflow.ellipsis),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          LayoutBuilder(
            builder: (context, constraints) {
              final split = constraints.maxWidth > 1180;
              final sidebar = _panel(
                title: 'Conversations',
                subtitle: 'Project-scoped threads',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    FilledButton.icon(
                      onPressed: project == null || _askingAi ? null : () async {
                        final created = await widget.client.createAiConversation(
                          _serviceUri,
                          projectId: project.projectId,
                          title: 'Conversation ${DateTime.now().toIso8601String().substring(11, 19)}',
                        );
                        final conversationId = _asString(created['conversation_id']);
                        if (conversationId.isNotEmpty) {
                          await _refreshAiWorkspace();
                          await _loadAiConversation(conversationId);
                        }
                      },
                      icon: const Icon(Icons.add_comment_outlined),
                      label: const Text('New conversation'),
                    ),
                    const SizedBox(height: 12),
                    for (final conversation in _aiConversations)
                      Card(
                        elevation: 0,
                        color: _selectedConversationId == conversation.conversationId ? const Color(0xFFE0F2F1) : const Color(0xFFF8FAFC),
                        child: ListTile(
                          dense: true,
                          onTap: () => _loadAiConversation(conversation.conversationId),
                          title: Text(conversation.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                          subtitle: Text('${conversation.turnCount} turns\n${conversation.model.isEmpty ? conversation.providerId : conversation.model}'),
                          isThreeLine: true,
                        ),
                      ),
                    if (_aiConversations.isEmpty) const Text('No conversations yet for this project.'),
                  ],
                ),
              );
              final workspace = Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _panel(
                    title: 'Question',
                    subtitle: 'Ask a bounded engineering question against the selected project.',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        DropdownButtonFormField<String>(
                          initialValue: _assistantMode,
                          decoration: const InputDecoration(labelText: 'Mode', border: OutlineInputBorder()),
                          items: const [
                            DropdownMenuItem(value: 'ask', child: Text('ASK')),
                            DropdownMenuItem(value: 'why_query', child: Text('WHY')),
                            DropdownMenuItem(value: 'impact_query', child: Text('IMPACT')),
                            DropdownMenuItem(value: 'change_query', child: Text('CHANGE')),
                            DropdownMenuItem(value: 'risk_query', child: Text('RISK')),
                            DropdownMenuItem(value: 'plan', child: Text('PLAN')),
                            DropdownMenuItem(value: 'architecture_explanation', child: Text('EXPLAIN')),
                            DropdownMenuItem(value: 'review', child: Text('REVIEW')),
                          ],
                          onChanged: (value) {
                            if (value == null) {
                              return;
                            }
                            setState(() {
                              _assistantMode = value;
                            });
                          },
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _assistantQuestionController,
                          minLines: 3,
                          maxLines: 7,
                          decoration: const InputDecoration(
                            labelText: 'Engineering question',
                            hintText: 'What should I work on next?',
                            border: OutlineInputBorder(),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 12,
                          runSpacing: 12,
                          children: [
                            FilledButton.icon(
                              onPressed: project == null || _askingAi ? null : _submitAiQuestion,
                              icon: const Icon(Icons.send),
                              label: Text(_askingAi ? 'Asking...' : 'Ask AI'),
                            ),
                            OutlinedButton.icon(
                              onPressed: project == null
                                  ? null
                                  : () {
                                      _assistantQuestionController.text = 'What should I work on next?';
                                      _assistantMode = 'plan';
                                      setState(() {});
                                    },
                              icon: const Icon(Icons.lightbulb_outline),
                              label: const Text('Use next-work prompt'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (response == null)
                    _panel(
                      title: 'Answer',
                      subtitle: 'No AI response yet.',
                      child: Text(
                        project == null
                            ? 'Select a project first.'
                            : 'Ask a question to generate a bounded response with evidence, citations, and unknowns.',
                      ),
                    )
                  else
                    _panel(
                      title: 'Answer',
                      subtitle: _asString(response['status'], 'response'),
                      child: SelectableText(_asString(response['answer'], '')),
                    ),
                  const SizedBox(height: 16),
                  LayoutBuilder(
                    builder: (context, inner) {
                      final stacked = inner.maxWidth < 980;
                      final evidencePanel = _panel(
                        title: 'Evidence',
                        subtitle: 'Context sources sent to the provider',
                        child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                            Text('Project summary: ${project?.projectId ?? _asString(responseContext['project_id'])}'),
                            const SizedBox(height: 8),
                            Text('Sources: ${_asList(responseContext['context_sources']).length}'),
                            const SizedBox(height: 8),
                            SelectableText(contextJson),
                          ],
                        ),
                      );
                      final citationsPanel = _panel(
                        title: 'Citations',
                        subtitle: '${citations.length} citation(s)',
                        child: citations.isEmpty
                            ? const Text('No citations were recorded for this response.')
                            : Column(
                                children: [
                                  for (final citation in citations)
                                    ListTile(
                                      dense: true,
                                      contentPadding: EdgeInsets.zero,
                                      title: Text(_asString(citation['title'], _asString(citation['entity_id'], 'Citation'))),
                                      subtitle: Text(
                                        '${_asString(citation['path'])}\n${_asString(citation['excerpt'])}',
                                        maxLines: 3,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                ],
                              ),
                      );
                      if (stacked) {
                        return Column(
                          children: [
                            evidencePanel,
                            const SizedBox(height: 16),
                            citationsPanel,
                          ],
                        );
                      }
                      return Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(child: evidencePanel),
                          const SizedBox(width: 16),
                          Expanded(child: citationsPanel),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 16),
                  LayoutBuilder(
                    builder: (context, inner) {
                      final stacked = inner.maxWidth < 980;
                      final left = Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          sectionList('Facts', facts, 'No explicit facts were returned.'),
                          const SizedBox(height: 16),
                          sectionList('Derived facts', derivedFacts, 'No derived facts were produced.'),
                        ],
                      );
                      final right = Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          sectionList('Inferences', inferences, 'No inferences were produced.'),
                          const SizedBox(height: 16),
                          sectionList('Recommendations', recommendations, 'No recommendations were produced.'),
                          const SizedBox(height: 16),
                          sectionList('Unknowns', unknowns, 'No unknowns were returned.'),
                        ],
                      );
                      if (stacked) {
                        return Column(
                          children: [
                            left,
                            const SizedBox(height: 16),
                            right,
                          ],
                        );
                      }
                      return Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(child: left),
                          const SizedBox(width: 16),
                          Expanded(child: right),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 16),
                  _panel(
                    title: 'Context inspector',
                    subtitle: 'Sanitized evidence bundle',
                    child: SelectableText(const JsonEncoder.withIndent('  ').convert(_aiResponse == null ? <String, dynamic>{} : _asMap(_aiResponse!['context_snapshot']))),
                  ),
                ],
              );
              if (split) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(width: 360, child: sidebar),
                    const SizedBox(width: 16),
                    Expanded(child: workspace),
                  ],
                );
              }
              return Column(
                children: [
                  sidebar,
                  const SizedBox(height: 16),
                  workspace,
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _settingsView() {
    final overview = _overview;
    final settings = _asMap(_aiSettings?['settings']);
    final providerHealth = _aiProviderHealth ?? const <String, dynamic>{};
    final providerOptions = <String>{
      'mock',
      'none',
      'compatible_http',
      _aiProviderController.text.trim(),
      _asString(settings['provider_id'], ''),
      ..._aiProviders.map((provider) => provider.providerId),
    }.where((value) => value.isNotEmpty).toList(growable: false);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Settings',
            subtitle: 'Service connection and local runtime preferences.',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: _serviceController,
                  decoration: const InputDecoration(
                    labelText: 'Service URL',
                    hintText: 'http://127.0.0.1:8765',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _refreshOverview(selectFirstProject: false),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    FilledButton.icon(
                      onPressed: () => _refreshOverview(selectFirstProject: false),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Reconnect'),
                    ),
                    OutlinedButton.icon(
                      onPressed: () {
                        _serviceController.text = widget.initialServiceUrl;
                        _refreshOverview(selectFirstProject: false);
                      },
                      icon: const Icon(Icons.restart_alt),
                      label: const Text('Reset to local default'),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _panel(
            title: 'AI settings',
            subtitle: 'Provider, model, endpoint and context budget.',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DropdownButtonFormField<String>(
                  initialValue: _aiProviderController.text.isEmpty ? _asString(settings['provider_id'], 'mock') : _aiProviderController.text,
                  items: providerOptions
                      .map((value) => DropdownMenuItem<String>(value: value, child: Text(value)))
                      .toList(growable: false),
                  onChanged: (value) {
                    if (value == null) {
                      return;
                    }
                    setState(() {
                      _aiProviderController.text = value;
                    });
                  },
                  decoration: const InputDecoration(
                    labelText: 'Provider',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _aiModelController,
                  decoration: const InputDecoration(
                    labelText: 'Model',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _aiEndpointController,
                  decoration: const InputDecoration(
                    labelText: 'Endpoint',
                    hintText: 'http://127.0.0.1:11434',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _aiTimeoutController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Timeout (seconds)',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: _aiContextBudgetController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Context budget',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: _aiMaxOutputController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Max output tokens',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    FilledButton.icon(
                      onPressed: _savingAiSettings ? null : _saveAiSettings,
                      icon: const Icon(Icons.save_outlined),
                      label: Text(_savingAiSettings ? 'Saving...' : 'Save AI settings'),
                    ),
                    _chip(_asString(providerHealth['message'], 'AI provider unavailable')),
                    _chip(_asString(providerHealth['kind'], _asString(providerHealth['provider_id'], 'unknown'))),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Service health', overview?.health, subtitle: 'Raw backend health payload.'),
          const SizedBox(height: 16),
          _jsonPanel('AI provider health', _aiProviderHealth, subtitle: 'Current provider status and capabilities.'),
          const SizedBox(height: 16),
          _jsonPanel('AI settings', _aiSettings, subtitle: 'Current AI configuration stored by the local service.'),
        ],
      ),
    );
  }

  Widget _pageForDestination() {
    switch (_destination) {
      case _Destination.home:
        return _homeView();
      case _Destination.projects:
        return _projectsView();
      case _Destination.portfolio:
        return PortfolioWorkspace(
          client: widget.client,
          serviceUri: _serviceUri,
          selectedProjectId: _selectedProjectId,
        );
      case _Destination.intelligence:
        return _projectPayloadView(
          title: 'Repository Intelligence',
          subtitle: 'Genome, memory and build intelligence from the local service.',
          keys: const ['genome', 'memory', 'build', 'configuration'],
        );
      case _Destination.graph:
        return _graphView();
      case _Destination.features:
        return _projectPayloadView(
          title: 'Features & Requirements',
          subtitle: 'Feature inventory, decisions and configuration evidence.',
          keys: const ['features', 'decisions', 'configuration'],
        );
      case _Destination.tests:
        return _projectPayloadView(
          title: 'Tests & Evidence',
          subtitle: 'Tests, documentation and APIs reported by the local service.',
          keys: const ['tests', 'documentation', 'apis', 'symbols'],
        );
      case _Destination.releases:
        return _projectPayloadView(
          title: 'Releases',
          subtitle: 'Flight snapshots, incidents and regressions for the selected project.',
          keys: const ['flight', 'flight_timeline', 'flight_snapshots', 'flight_incidents', 'flight_regressions'],
        );
      case _Destination.timeline:
        return _projectPayloadView(
          title: 'Timeline',
          subtitle: 'Memory and flight history side by side.',
          keys: const ['memory_timeline', 'flight_timeline'],
        );
      case _Destination.documentation:
        return _projectPayloadView(
          title: 'Documentation',
          subtitle: 'Documentation inventory and related structural evidence.',
          keys: const ['documentation', 'build'],
        );
      case _Destination.assistant:
        return _assistantView();
      case _Destination.plugins:
        return const Center(child: Text('Plugin surface is reserved for future integrations.'));
      case _Destination.health:
        return _settingsView();
      case _Destination.settings:
        return _settingsView();
    }
  }

  Widget _topBar(BuildContext context) {
    final selectedProject = _selectedOverview();
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Color(0xFFE2E8F0))),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 1100;
          final title = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('NEOS', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
              Text('Windows desktop engineering shell', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.black54)),
            ],
          );
          final controls = compact
              ? Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    TextField(
                      controller: _serviceController,
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.link_outlined),
                        hintText: 'http://127.0.0.1:8765',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      onSubmitted: (_) => _refreshOverview(selectFirstProject: false),
                    ),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: () => _refreshOverview(selectFirstProject: false),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Refresh'),
                    ),
                  ],
                )
              : Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _serviceController,
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.link_outlined),
                          hintText: 'http://127.0.0.1:8765',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                        onSubmitted: (_) => _refreshOverview(selectFirstProject: false),
                      ),
                    ),
                    const SizedBox(width: 12),
                    FilledButton.icon(
                      onPressed: () => _refreshOverview(selectFirstProject: false),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Refresh'),
                    ),
                  ],
                );
          final statusChips = Wrap(
            spacing: 8,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              _chip(
                _overview == null
                    ? 'Disconnected'
                    : '${selectedProject?.name ?? _overview!.serviceName} / ${_overview!.status}',
              ),
              if (_selectedProjectId != null) _chip('Selected $_selectedProjectId'),
              if (_loadingOverview) const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
              if (_loadingProject) const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
              if (_error != null)
                Chip(
                  backgroundColor: const Color(0xFFFEE2E2),
                  label: Text(
                    _error!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
          );
          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                title,
                const SizedBox(height: 12),
                controls,
                const SizedBox(height: 10),
                statusChips,
              ],
            );
          }
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  title,
                  const SizedBox(width: 24),
                  Expanded(child: controls),
                ],
              ),
              const SizedBox(height: 10),
              statusChips,
            ],
          );
        },
      ),
    );
  }

  Widget _contentArea(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 180),
      child: _pageForDestination(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _topBar(context),
            Expanded(
              child: Row(
                children: [
                  _navigationPane(),
                  Expanded(child: _contentArea(context)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Bullet extends StatelessWidget {
  const _Bullet({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(top: 7),
            child: Icon(Icons.circle, size: 8, color: Color(0xFF0F766E)),
          ),
          const SizedBox(width: 10),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}
