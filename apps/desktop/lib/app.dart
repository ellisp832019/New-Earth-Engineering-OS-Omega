import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'decision_center.dart';
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
  today,
  projects,
  portfolio,
  requirements,
  architecture,
  hardware,
  registry,
  workspace,
  firmware,
  decisions,
  evidence,
  timeline,
  workQueue,
  assistant,
  health,
  settings,
}

class _NavItem {
  const _NavItem(this.destination, this.icon, this.label);

  final _Destination destination;
  final IconData icon;
  final String label;
}

class _OpenCommandPaletteIntent extends Intent {
  const _OpenCommandPaletteIntent();
}

class _RefreshWorkspaceIntent extends Intent {
  const _RefreshWorkspaceIntent();
}

class NeosApp extends StatelessWidget {
  const NeosApp({super.key, required this.client});

  final NeosClient client;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NEOS Command Centre',
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
  final TextEditingController _commandSearchController = TextEditingController();
  final TextEditingController _assistantQuestionController = TextEditingController(text: 'What should I work on next?');
  final TextEditingController _aiProviderController = TextEditingController();
  final TextEditingController _aiModelController = TextEditingController();
  final TextEditingController _aiEndpointController = TextEditingController();
  final TextEditingController _aiTimeoutController = TextEditingController();
  final TextEditingController _aiContextBudgetController = TextEditingController();
  final TextEditingController _aiMaxOutputController = TextEditingController();

  _Destination _destination = _Destination.today;
  ServiceOverview? _overview;
  ProjectRecord? _project;
  Map<String, dynamic>? _todayBrief;
  Map<String, dynamic>? _workQueue;
  Map<String, dynamic>? _sessionState;
  List<Map<String, dynamic>> _searchResults = const [];
  String? _selectedProjectId;
  String? _error;
  String? _commandError;
  bool _loadingOverview = true;
  bool _loadingProject = false;
  bool _loadingCommandCentre = false;
  bool _searchingCommandCentre = false;
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
    _NavItem(_Destination.today, Icons.today_outlined, 'Today'),
    _NavItem(_Destination.projects, Icons.folder_outlined, 'Projects'),
    _NavItem(_Destination.portfolio, Icons.account_tree_outlined, 'Portfolio'),
    _NavItem(_Destination.workQueue, Icons.inbox_outlined, 'Work Queue'),
    _NavItem(_Destination.requirements, Icons.rule_outlined, 'Requirements'),
    _NavItem(_Destination.architecture, Icons.graphic_eq_outlined, 'Architecture'),
    _NavItem(_Destination.hardware, Icons.precision_manufacturing_outlined, 'Hardware Centre'),
    _NavItem(_Destination.registry, Icons.account_tree_outlined, 'Registry Centre'),
    _NavItem(_Destination.workspace, Icons.dashboard_outlined, 'Workspace'),
    _NavItem(_Destination.firmware, Icons.memory_outlined, 'Firmware Centre'),
    _NavItem(_Destination.decisions, Icons.rule_folder_outlined, 'Decisions'),
    _NavItem(_Destination.evidence, Icons.fact_check_outlined, 'Evidence'),
    _NavItem(_Destination.timeline, Icons.timeline_outlined, 'Timeline'),
    _NavItem(_Destination.assistant, Icons.psychology_outlined, 'AI Partner'),
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
    _commandSearchController.dispose();
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
        await _saveWorkspaceSession();
        await _refreshCommandCentre();
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
      await _saveWorkspaceSession();
      await _refreshCommandCentre();
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
    unawaited(_saveWorkspaceSession());
    if (destination == _Destination.today || destination == _Destination.workQueue || destination == _Destination.projects) {
      unawaited(_refreshCommandCentre());
    }
    if (destination == _Destination.hardware || destination == _Destination.registry || destination == _Destination.firmware) {
      unawaited(_saveWorkspaceSession());
    }
    if (destination == _Destination.assistant || destination == _Destination.settings || destination == _Destination.health) {
      unawaited(_refreshAiWorkspace());
    }
  }

  Future<void> _saveWorkspaceSession() async {
    try {
      await widget.client.saveAppSession(_serviceUri, {
        'selected_project_id': _selectedProjectId,
        'destination': _destination.name,
        'updated_at': DateTime.now().toIso8601String(),
      });
    } catch (_) {
      // Session persistence should not block the shell.
    }
  }

  Future<void> _refreshCommandCentre() async {
    setState(() {
      _loadingCommandCentre = true;
      _commandError = null;
    });
    try {
      final results = await Future.wait([
        widget.client.loadToday(_serviceUri, projectIds: _selectedProjectId == null ? null : <String>[_selectedProjectId!]),
        widget.client.loadWorkQueue(_serviceUri, projectIds: _selectedProjectId == null ? null : <String>[_selectedProjectId!]),
        widget.client.loadAppSession(_serviceUri),
      ]);
      setState(() {
        _todayBrief = _asMap(results[0]);
        _workQueue = _asMap(results[1]);
        _sessionState = _asMap(results[2]);
        _loadingCommandCentre = false;
      });
    } catch (error) {
      setState(() {
        _loadingCommandCentre = false;
        _commandError = error.toString();
      });
    }
  }

  Future<void> _runCommandSearch(String query) async {
    final trimmed = query.trim();
    if (trimmed.isEmpty) {
      setState(() {
        _searchResults = const [];
      });
      return;
    }
    setState(() {
      _searchingCommandCentre = true;
      _commandError = null;
    });
    try {
      final response = await widget.client.searchCommandCentre(
        _serviceUri,
        trimmed,
        projectIds: _selectedProjectId == null ? null : <String>[_selectedProjectId!],
        limit: 12,
      );
      setState(() {
        _searchResults = _asList(response['items']).map((item) => _asMap(item)).toList(growable: false);
        _searchingCommandCentre = false;
      });
    } catch (error) {
      setState(() {
        _searchingCommandCentre = false;
        _commandError = error.toString();
      });
    }
  }

  Future<void> _openCommandPalette() async {
    _commandSearchController.text = _commandSearchController.text.trim();
    if (!mounted) {
      return;
    }
    await showDialog<void>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return Dialog(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 860, maxHeight: 720),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Command Palette', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _commandSearchController,
                        autofocus: true,
                        decoration: const InputDecoration(
                          labelText: 'Search commands or evidence',
                          border: OutlineInputBorder(),
                        ),
                        onSubmitted: (value) async {
                          await _runCommandSearch(value);
                          setDialogState(() {});
                        },
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          OutlinedButton(onPressed: () => _selectDestination(_Destination.today), child: const Text('Today')),
                          OutlinedButton(onPressed: () => _selectDestination(_Destination.workQueue), child: const Text('Work Queue')),
                          OutlinedButton(onPressed: () => _selectDestination(_Destination.projects), child: const Text('Projects')),
                          OutlinedButton(onPressed: () => _selectDestination(_Destination.hardware), child: const Text('Hardware Centre')),
                          OutlinedButton(onPressed: () => _selectDestination(_Destination.registry), child: const Text('Registry Centre')),
                          OutlinedButton(onPressed: () => _selectDestination(_Destination.firmware), child: const Text('Firmware Centre')),
                          OutlinedButton(onPressed: () => _selectDestination(_Destination.assistant), child: const Text('AI Partner')),
                        ],
                      ),
                      const SizedBox(height: 16),
                      if (_searchingCommandCentre) const LinearProgressIndicator(),
                      if (_commandError != null) ...[
                        const SizedBox(height: 8),
                        Text(_commandError!, style: const TextStyle(color: Colors.red)),
                      ],
                      const SizedBox(height: 12),
                      Expanded(
                        child: ListView(
                          children: [
                            for (final result in _searchResults)
                              ListTile(
                                leading: const Icon(Icons.search),
                                title: Text(_asString(result['title'], 'Result')),
                                subtitle: Text('${_asString(result['kind'])} · ${_asString(result['snippet'])}'),
                                onTap: () => Navigator.of(context).pop(),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
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
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
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
      ),
    );
  }

  Widget _todayView() {
    final overview = _overview;
    final project = _project;
    final today = _todayBrief;
    final queue = _workQueue;
    if (_loadingOverview && overview == null) {
      return const Center(child: CircularProgressIndicator());
    }
    final workItems = _asList(queue?['items']).map((item) => _asMap(item)).toList(growable: false);
    final projectBriefs = _asList(today?['projects']).map((item) => _asMap(item)).toList(growable: false);
    final highlights = _asList(today?['highlights']).map((item) => _asMap(item)).toList(growable: false);
    final commandHealth = _asMap(today?['command_centre_health']);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Today',
            subtitle: 'Deterministic daily brief, open work, and command-centre controls.',
            trailing: Wrap(
              spacing: 8,
              children: [
                IconButton(
                  onPressed: _openCommandPalette,
                  icon: const Icon(Icons.search),
                  tooltip: 'Command palette',
                ),
                IconButton(
                  onPressed: () => _refreshOverview(selectFirstProject: false),
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Refresh',
                ),
              ],
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
                  value: (overview?.projects.length ?? projectBriefs.length).toString(),
                  subtitle: 'Registered in the local database',
                  icon: Icons.folder_copy_outlined,
                ),
                _metricCard(
                  title: 'Open work',
                  value: (queue?['count'] ?? workItems.length).toString(),
                  subtitle: 'Active queue items',
                  icon: Icons.inbox_outlined,
                ),
                _metricCard(
                  title: 'Selected project',
                  value: project?.projectId ?? _asString(today?['selected_project_id'], 'none'),
                  subtitle: project?.summary['name']?.toString() ?? 'Choose a project from the sidebar',
                  icon: Icons.hub_outlined,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          LayoutBuilder(
            builder: (context, constraints) {
              final split = constraints.maxWidth > 1180;
              final brief = _panel(
                title: 'Daily brief',
                subtitle: 'Selected project, system freshness, and recommended focus.',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_commandError != null) ...[
                      Text(_commandError!, style: const TextStyle(color: Colors.red)),
                      const SizedBox(height: 8),
                    ],
                    _chip('Session ${_asString(_asMap(_sessionState)['session_key'], 'workspace')}'),
                    const SizedBox(height: 12),
                    for (final item in highlights)
                      ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.bolt_outlined),
                        title: Text(_asString(item['title'], 'Work item')),
                        subtitle: Text(_asString(item['why'], '')),
                      ),
                    if (highlights.isEmpty)
                      const Text('No current highlights. Refresh the queue to generate deterministic next actions.'),
                  ],
                ),
              );
              final health = _panel(
                title: 'Command-centre health',
                subtitle: 'Persistence, refresh jobs, and queue status.',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _chip('Open ${_asInt(commandHealth['open_work_items'], workItems.length)}'),
                    _chip('Sessions ${_asInt(commandHealth['session_count'])}'),
                    _chip('Refresh jobs ${_asInt(commandHealth['active_refresh_jobs'])}'),
                    const SizedBox(height: 12),
                    SelectableText(_prettyJson(commandHealth)),
                  ],
                ),
              );
              if (split) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: brief),
                    const SizedBox(width: 16),
                    Expanded(child: health),
                  ],
                );
              }
              return Column(
                children: [
                  brief,
                  const SizedBox(height: 16),
                  health,
                ],
              );
            },
          ),
          const SizedBox(height: 16),
          _panel(
            title: 'Open work',
            subtitle: 'Active deterministic queue items generated from current project intelligence.',
            trailing: TextButton.icon(
              onPressed: () => _selectDestination(_Destination.workQueue),
              icon: const Icon(Icons.open_in_new),
              label: const Text('Open full queue'),
            ),
            child: workItems.isEmpty
                ? const Text('No open queue items yet.')
                : Column(
                    children: [
                      for (final item in workItems.take(5))
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: Icon(
                            Icons.circle,
                            size: 12,
                            color: _asString(item['priority']) == 'high'
                                ? const Color(0xFFDC2626)
                                : _asString(item['priority']) == 'medium'
                                    ? const Color(0xFFD97706)
                                    : const Color(0xFF0F766E),
                          ),
                          title: Text(_asString(item['title'], 'Work item')),
                          subtitle: Text(_asString(item['why'], '')),
                          trailing: Text(_asString(item['status'], 'open')),
                          onTap: () => _selectDestination(_Destination.workQueue),
                        ),
                    ],
                  ),
          ),
          const SizedBox(height: 16),
          if (projectBriefs.isNotEmpty)
            _panel(
              title: 'Project watchlist',
              subtitle: 'Freshness and queue pressure across registered projects.',
              child: Column(
                children: [
                  for (final item in projectBriefs.take(6))
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      onTap: () => _loadProject(_asString(item['project_id'])),
                      leading: const Icon(Icons.folder_outlined),
                      title: Text(_asString(item['name'], _asString(item['project_id']))),
                      subtitle: Text('Work ${_asInt(item['work_item_count'])} · Freshness ${_asString(item['scan_freshness'], 'unknown')}'),
                      trailing: Text(_asString(item['status'], 'unknown')),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _workQueueView() {
    final queue = _workQueue ?? const <String, dynamic>{};
    final items = _asList(queue['items']).map((item) => _asMap(item)).toList(growable: false);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Work Queue',
            subtitle: 'Deterministic, stateful work items derived from current project intelligence.',
            trailing: Wrap(
              spacing: 8,
              children: [
                IconButton(
                  onPressed: () => _refreshCommandCentre(),
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Refresh queue',
                ),
                IconButton(
                  onPressed: _openCommandPalette,
                  icon: const Icon(Icons.search),
                  tooltip: 'Search command centre',
                ),
              ],
            ),
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip('Open ${_asInt(_asMap(queue['summary'])['open_count'], items.length)}'),
                _chip('High priority ${_asInt(_asMap(queue['summary'])['high_priority_count'])}'),
                _chip('Projects ${_asInt(_asMap(queue['summary'])['project_count'])}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (_loadingCommandCentre) const LinearProgressIndicator(),
          if (items.isEmpty)
            _panel(
              title: 'Queue items',
              subtitle: 'Nothing actionable is currently open.',
              child: const Text('Refresh the queue after a scan or release to repopulate actionable items.'),
            )
          else
            Column(
              children: [
                for (final item in items)
                  Card(
                    elevation: 0,
                    color: const Color(0xFFF8FAFC),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
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
                                    Text(_asString(item['title'], 'Work item'), style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                                    const SizedBox(height: 4),
                                    Text(_asString(item['why'], ''), style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.black54)),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 12),
                              _chip(_asString(item['priority'], 'medium')),
                            ],
                          ),
                          const SizedBox(height: 12),
                          SelectableText(_prettyJson(item['evidence_json'])),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              OutlinedButton(
                                onPressed: () async {
                                  await widget.client.acknowledgeWorkItem(_serviceUri, _asString(item['id']));
                                  await _refreshCommandCentre();
                                },
                                child: const Text('Acknowledge'),
                              ),
                              OutlinedButton(
                                onPressed: () async {
                                  await widget.client.deferWorkItem(_serviceUri, _asString(item['id']));
                                  await _refreshCommandCentre();
                                },
                                child: const Text('Defer'),
                              ),
                              OutlinedButton(
                                onPressed: () async {
                                  await widget.client.dismissWorkItem(_serviceUri, _asString(item['id']));
                                  await _refreshCommandCentre();
                                },
                                child: const Text('Dismiss'),
                              ),
                              FilledButton(
                                onPressed: () async {
                                  await widget.client.resolveWorkItem(_serviceUri, _asString(item['id']));
                                  await _refreshCommandCentre();
                                },
                                child: const Text('Resolve'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _healthView() {
    final overview = _overview;
    final commandHealth = _asMap(_todayBrief?['command_centre_health']);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'System Health',
            subtitle: 'Service, storage, command-centre, and AI runtime status.',
            trailing: IconButton(
              onPressed: () {
                _refreshOverview(selectFirstProject: false);
                _refreshCommandCentre();
                _refreshAiWorkspace();
              },
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
                  title: 'Schema',
                  value: _asString(overview?.schema['database_schema'], 'n/a'),
                  subtitle: 'Database schema version',
                  icon: Icons.data_object_outlined,
                ),
                _metricCard(
                  title: 'Open work',
                  value: _asString(commandHealth['open_work_items'], '0'),
                  subtitle: 'Command-centre queue',
                  icon: Icons.inbox_outlined,
                ),
                _metricCard(
                  title: 'AI provider',
                  value: _asString(_aiProviderHealth?['healthy'], 'false'),
                  subtitle: _asString(_aiProviderHealth?['message'], 'Provider status unavailable'),
                  icon: Icons.psychology_outlined,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Service health', overview?.health, subtitle: 'Raw backend health payload.'),
          const SizedBox(height: 16),
          _jsonPanel('Command-centre health', commandHealth, subtitle: 'Queue, session, and refresh job status.'),
          const SizedBox(height: 16),
          _jsonPanel('AI provider health', _aiProviderHealth, subtitle: 'Current provider status and capabilities.'),
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

  Widget _requirementsView() {
    final project = _project;
    if (project == null) {
      return const Center(child: Text('Select a project to inspect requirements traceability.'));
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Requirements Intelligence',
            subtitle: 'Deterministic intent, implementation and verification traceability for the selected project.',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip(project.projectId),
                _chip('Requirements ${_countOf(project.section('requirements'))}'),
                _chip('Gaps ${_countOf(project.section('requirement_gaps'))}'),
                _chip('Verification ${_countOf(project.section('requirement_verification'))}'),
                _chip('Architecture gaps ${_countOf(project.section('requirement_architecture_gaps'))}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Requirements intelligence', project.section('requirements'), subtitle: 'Combined extracted and persisted requirement records.'),
          const SizedBox(height: 16),
          _jsonPanel('Requirement gaps', project.section('requirement_gaps'), subtitle: 'Requirements missing feature, architecture, test, validation, or release evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Verification readiness', project.section('requirement_verification'), subtitle: 'Requirements with complete traceability to implementation and validation evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Architecture without requirement', project.section('requirement_architecture_gaps'), subtitle: 'Architecture components that are not tied back to a requirement yet.'),
          const SizedBox(height: 16),
          _jsonPanel('Unimplemented requirements', project.section('requirement_unimplemented'), subtitle: 'Requirements that do not yet link to a feature or architecture component.'),
          const SizedBox(height: 16),
          _jsonPanel('Untested requirements', project.section('requirement_untested'), subtitle: 'Requirements without test evidence in the current trace set.'),
          const SizedBox(height: 16),
          _jsonPanel('Requirement history', project.section('requirement_history'), subtitle: 'Review and operator history for the selected project.'),
        ],
      ),
    );
  }

  Widget _hardwareView() {
    final project = _project;
    if (project == null) {
      return const Center(child: Text('Select a project to inspect hardware intelligence.'));
    }
    final hardware = _asMap(project.section('hardware'));
    final summary = _asMap(hardware['summary']);
    final boards = _asList(hardware['boards']).map((item) => _asMap(item)).toList(growable: false);
    final components = _asList(hardware['components']).map((item) => _asMap(item)).toList(growable: false);
    final pins = _asList(hardware['pins']).map((item) => _asMap(item)).toList(growable: false);
    final validations = _asList(hardware['validations']).map((item) => _asMap(item)).toList(growable: false);
    final gaps = _asList(hardware['gaps']).map((item) => _asMap(item)).toList(growable: false);
    final risks = _asList(hardware['risks']).map((item) => _asMap(item)).toList(growable: false);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Hardware Centre',
            subtitle: 'Evidence-backed physical engineering snapshot for the selected project.',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip(project.projectId),
                _chip('Boards ${_asInt(summary['board_count'])}'),
                _chip('Components ${_asInt(summary['component_count'])}'),
                _chip('Pins ${_asInt(summary['pin_mapping_count'])}'),
                _chip('Validation ${_asString(summary['validation_state'], 'unknown')}'),
                _chip('Gaps ${_asInt(summary['gap_count'])}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Hardware summary', summary, subtitle: 'Conservative derived summary for the selected repository evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Boards', boards, subtitle: 'Discovered board and board revision evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Components', components, subtitle: 'Physical part identity evidence derived from BOM and related files.'),
          const SizedBox(height: 16),
          _jsonPanel('Pin mappings', pins, subtitle: 'Explicit firmware-to-hardware pin evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Validation', validations, subtitle: 'Hardware validation and bring-up evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Risks', risks, subtitle: 'Conservative hardware risks and review items.'),
          const SizedBox(height: 16),
          _jsonPanel('Gaps', gaps, subtitle: 'Missing or incomplete physical engineering evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Raw hardware payload', hardware, subtitle: 'Full hardware snapshot returned by the backend.'),
        ],
      ),
    );
  }

  Widget _registryView() {
    final project = _project;
    if (project == null) {
      return const Center(child: Text('Select a project to inspect registry and contract intelligence.'));
    }
    final registry = _asMap(project.section('registry'));
    final identity = _asMap(registry['identity']);
    final contracts = _asMap(registry['contracts']);
    final drift = _asMap(registry['drift']);
    final impact = _asMap(registry['impact']);
    final health = _asMap(registry['health']);
    final conflicts = _asList(registry['identity_conflicts']).map((item) => _asMap(item)).toList(growable: false);
    final sources = _asList(registry['sources']).map((item) => _asMap(item)).toList(growable: false);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Registry Centre',
            subtitle: 'Stable identity, contract spine, drift and impact analysis for the selected project.',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip(project.projectId),
                _chip('Contracts ${_asInt(health['contract_count'])}'),
                _chip('Sources ${_asInt(health['discovered_contract_count'])}'),
                _chip('Conflicts ${_asInt(health['identity_conflict_count'])}'),
                _chip('Drift ${_countOf(drift)}'),
                _chip('Status ${_asString(health['status'], 'unknown')}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Identity', identity, subtitle: 'Stable project identity with declared, observed and derived repository evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Contracts', contracts, subtitle: 'Project, capabilities, dependencies, safety boundary and release-state contracts.'),
          const SizedBox(height: 16),
          _jsonPanel('Drift', drift, subtitle: 'Conservative contract drift classification and review state.'),
          const SizedBox(height: 16),
          _jsonPanel('Impact', impact, subtitle: 'Architecture impact analysis and cross-project reasoning payload.'),
          const SizedBox(height: 16),
          _jsonPanel('Identity conflicts', conflicts, subtitle: 'Repository and alias ambiguities that require review rather than auto-resolution.'),
          const SizedBox(height: 16),
          _jsonPanel('Discovered sources', sources, subtitle: 'Structured manifest and contract files discovered deterministically from the repository.'),
          const SizedBox(height: 16),
          _jsonPanel('Raw registry payload', registry, subtitle: 'Full registry snapshot returned by the backend.'),
        ],
      ),
    );
  }

  Widget _workspaceView() {
    final project = _project;
    if (project == null) {
      return const Center(child: Text('Select a project to inspect workspace intelligence.'));
    }
    final workspace = _asMap(project.section('workspace'));
    final summary = _asMap(workspace['summary']);
    final classification = _asMap(workspace['classification']);
    final integration = _asMap(workspace['integration']);
    final contract = _asMap(workspace['contract']);
    final repository = _asMap(workspace['repository']);
    final dependencies = _asMap(workspace['dependencies']);
    final freshness = _asMap(workspace['freshness']);
    final release = _asMap(workspace['release']);
    final safety = _asMap(workspace['safety']);
    final provenance = _asMap(workspace['provenance']);
    final evidence = _asMap(workspace['evidence']);
    final attention = _asList(workspace['attention']).map((item) => _asMap(item)).toList(growable: false);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Workspace Centre',
            subtitle: 'Deterministic project classification, contract adapter and readiness view.',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip(project.projectId),
                _chip(_asString(classification['classification'], 'unknown')),
                _chip('Integration ${_asString(integration['mode'], 'unknown')}'),
                _chip('Readiness ${_asString(integration['readiness'], 'unknown')}'),
                _chip('Freshness ${_asString(freshness['status'], 'unknown')}'),
                _chip('Attention ${attention.length}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Workspace summary', summary, subtitle: 'Compact workspace state used by the navigation and backend API.'),
          const SizedBox(height: 16),
          _jsonPanel('Classification', classification, subtitle: 'Deterministic project classification and first-party filter state.'),
          const SizedBox(height: 16),
          _jsonPanel('Integration', integration, subtitle: 'Contracted, observed or degraded integration state and readiness.'),
          const SizedBox(height: 16),
          _jsonPanel('Contract adapter', contract, subtitle: 'Platform Core contract adapter with registry and manifest evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Repository', repository, subtitle: 'Declared and observed repository state, including freshness inputs.'),
          const SizedBox(height: 16),
          _jsonPanel('Dependencies', dependencies, subtitle: 'Declared, observed and reconciled dependency state.'),
          const SizedBox(height: 16),
          _jsonPanel('Freshness', freshness, subtitle: 'Current-vs-scan freshness and repository recency state.'),
          const SizedBox(height: 16),
          _jsonPanel('Release', release, subtitle: 'Release-readiness state carried into the workspace view.'),
          const SizedBox(height: 16),
          _jsonPanel('Safety', safety, subtitle: 'Conservative safety boundary summary for the selected project.'),
          const SizedBox(height: 16),
          _jsonPanel('Provenance', provenance, subtitle: 'Declared, observed and derived evidence sources.'),
          const SizedBox(height: 16),
          _jsonPanel('Evidence', evidence, subtitle: 'Presence flags for the major workspace evidence sources.'),
          const SizedBox(height: 16),
          _jsonPanel('Attention', attention, subtitle: 'Deterministic review items that need operator attention.'),
          const SizedBox(height: 16),
          _jsonPanel('Raw workspace payload', workspace, subtitle: 'Full workspace snapshot returned by the backend.'),
        ],
      ),
    );
  }

  Widget _firmwareView() {
    final project = _project;
    if (project == null) {
      return const Center(child: Text('Select a project to inspect firmware intelligence.'));
    }
    final firmware = _asMap(project.section('firmware'));
    final summary = _asMap(firmware['summary']);
    final targets = _asList(firmware['targets']).map((item) => _asMap(item)).toList(growable: false);
    final buildVariants = _asList(firmware['build_variants']).map((item) => _asMap(item)).toList(growable: false);
    final environments = _asList(firmware['environments']).map((item) => _asMap(item)).toList(growable: false);
    final modules = _asList(firmware['modules']).map((item) => _asMap(item)).toList(growable: false);
    final tasks = _asList(firmware['tasks']).map((item) => _asMap(item)).toList(growable: false);
    final rtosPrimitives = _asList(firmware['rtos_primitives']).map((item) => _asMap(item)).toList(growable: false);
    final interrupts = _asList(firmware['interrupts']).map((item) => _asMap(item)).toList(growable: false);
    final timers = _asList(firmware['timers']).map((item) => _asMap(item)).toList(growable: false);
    final timingFacts = _asList(firmware['timing_facts']).map((item) => _asMap(item)).toList(growable: false);
    final states = _asList(firmware['state_machines']).map((item) => _asMap(item)).toList(growable: false);
    final peripherals = _asList(firmware['peripherals']).map((item) => _asMap(item)).toList(growable: false);
    final buses = _asList(firmware['buses']).map((item) => _asMap(item)).toList(growable: false);
    final gpio = _asList(firmware['gpio']).map((item) => _asMap(item)).toList(growable: false);
    final gpioConflicts = _asList(firmware['gpio_conflicts']).map((item) => _asMap(item)).toList(growable: false);
    final protocols = _asList(firmware['protocols']).map((item) => _asMap(item)).toList(growable: false);
    final packets = _asList(firmware['packets']).map((item) => _asMap(item)).toList(growable: false);
    final memory = _asList(firmware['memory_findings']).map((item) => _asMap(item)).toList(growable: false);
    final findings = _asList(firmware['findings']).map((item) => _asMap(item)).toList(growable: false);
    final compatibility = _asList(firmware['compatibility']).map((item) => _asMap(item)).toList(growable: false);
    final validations = _asList(firmware['validations']).map((item) => _asMap(item)).toList(growable: false);
    final risks = _asList(firmware['risks']).map((item) => _asMap(item)).toList(growable: false);
    final gaps = _asList(firmware['gaps']).map((item) => _asMap(item)).toList(growable: false);
    final parsers = _asList(firmware['supported_parsers']).map((item) => item.toString()).toList(growable: false);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'Firmware Centre',
            subtitle: 'Deterministic embedded firmware intelligence for the selected project.',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chip(project.projectId),
                _chip('Parsers ${parsers.length}'),
                _chip('Environments ${_asInt(summary['environment_count'])}'),
                _chip('Targets ${_asInt(summary['target_count'])}'),
                _chip('Tasks ${_asInt(summary['task_count'])}'),
                _chip('RTOS ${_asInt(summary['rtos_primitive_count'])}'),
                _chip('Compatibility ${_asString(summary['compatibility_state'], 'unknown')}'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Firmware summary', summary, subtitle: 'Deterministic snapshot of build, target, timing, and validation evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Supported parsers', parsers, subtitle: 'Source parsers that were actually detected in the repository.'),
          const SizedBox(height: 16),
          _jsonPanel('Targets', targets, subtitle: 'MCU and board targets derived from the parsed firmware build configuration.'),
          const SizedBox(height: 16),
          _jsonPanel('Build variants', buildVariants, subtitle: 'Resolved build variants and compile-time flags per environment.'),
          const SizedBox(height: 16),
          _jsonPanel('Environments', environments, subtitle: 'PlatformIO or embedded build environments and inheritance details.'),
          const SizedBox(height: 16),
          _jsonPanel('Modules', modules, subtitle: 'Source modules and configuration files participating in firmware analysis.'),
          const SizedBox(height: 16),
          _jsonPanel('Tasks', tasks, subtitle: 'Detected task or thread evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('RTOS primitives', rtosPrimitives, subtitle: 'Queues, semaphores, mutexes, event groups, and task notifications.'),
          const SizedBox(height: 16),
          _jsonPanel('Interrupts', interrupts, subtitle: 'Detected interrupt handler evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Timers', timers, subtitle: 'Detected timer and periodic scheduling evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Timing facts', timingFacts, subtitle: 'Explicit delays, waits, and watchdog-related timing evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('State machines', states, subtitle: 'Explicit or conservative state-machine evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Peripherals', peripherals, subtitle: 'Peripheral configuration evidence inferred from static source inspection.'),
          const SizedBox(height: 16),
          _jsonPanel('Buses', buses, subtitle: 'Bus configuration evidence for I2C, SPI, UART, and similar transports.'),
          const SizedBox(height: 16),
          _jsonPanel('GPIO', gpio, subtitle: 'GPIO ownership and pin symbol evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('GPIO conflicts', gpioConflicts, subtitle: 'Potential mismatches between firmware GPIO usage and hardware mappings.'),
          const SizedBox(height: 16),
          _jsonPanel('Protocols', protocols, subtitle: 'Protocol and transport evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Packets', packets, subtitle: 'Detected packet or message structure definitions.'),
          const SizedBox(height: 16),
          _jsonPanel('Memory', memory, subtitle: 'Memory and buffer findings.'),
          const SizedBox(height: 16),
          _jsonPanel('Findings', findings, subtitle: 'Derived firmware findings and review items.'),
          const SizedBox(height: 16),
          _jsonPanel('Compatibility', compatibility, subtitle: 'Firmware variant to hardware revision compatibility records.'),
          const SizedBox(height: 16),
          _jsonPanel('Validation', validations, subtitle: 'Firmware analysis and validation evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Risks', risks, subtitle: 'Conservative firmware review items and risk indicators.'),
          const SizedBox(height: 16),
          _jsonPanel('Gaps', gaps, subtitle: 'Missing or incomplete firmware evidence.'),
          const SizedBox(height: 16),
          _jsonPanel('Raw firmware payload', firmware, subtitle: 'Full firmware snapshot returned by the backend.'),
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
      case _Destination.today:
        return _todayView();
      case _Destination.projects:
        return _projectsView();
      case _Destination.portfolio:
        return PortfolioWorkspace(
          client: widget.client,
          serviceUri: _serviceUri,
          selectedProjectId: _selectedProjectId,
        );
      case _Destination.workQueue:
        return _workQueueView();
      case _Destination.requirements:
        return _requirementsView();
      case _Destination.architecture:
        return _graphView();
      case _Destination.hardware:
        return _hardwareView();
      case _Destination.registry:
        return _registryView();
      case _Destination.workspace:
        return _workspaceView();
      case _Destination.firmware:
        return _firmwareView();
      case _Destination.decisions:
        return DecisionCentre(
          client: widget.client,
          serviceUri: _serviceUri,
          selectedProjectId: _selectedProjectId,
        );
      case _Destination.evidence:
        return _projectPayloadView(
          title: 'Evidence',
          subtitle: 'Tests, documentation, APIs, and symbols reported by the local service.',
          keys: const ['tests', 'documentation', 'apis', 'symbols'],
        );
      case _Destination.timeline:
        return _projectPayloadView(
          title: 'Timeline',
          subtitle: 'Memory and flight history side by side.',
          keys: const ['memory_timeline', 'flight_timeline'],
        );
      case _Destination.assistant:
        return _assistantView();
      case _Destination.health:
        return _healthView();
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
              Text('NEOS Command Centre', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
              Text('Windows desktop engineering cockpit', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.black54)),
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
                    const SizedBox(height: 8),
                    OutlinedButton.icon(
                      onPressed: _openCommandPalette,
                      icon: const Icon(Icons.search),
                      label: const Text('Command palette'),
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
                    const SizedBox(width: 12),
                    OutlinedButton.icon(
                      onPressed: _openCommandPalette,
                      icon: const Icon(Icons.search),
                      label: const Text('Command palette'),
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
    return Shortcuts(
      shortcuts: <ShortcutActivator, Intent>{
        const SingleActivator(LogicalKeyboardKey.keyK, control: true): const _OpenCommandPaletteIntent(),
        const SingleActivator(LogicalKeyboardKey.keyR, control: true): const _RefreshWorkspaceIntent(),
      },
      child: Actions(
        actions: <Type, Action<Intent>>{
          _OpenCommandPaletteIntent: CallbackAction<_OpenCommandPaletteIntent>(onInvoke: (_) {
            unawaited(_openCommandPalette());
            return null;
          }),
          _RefreshWorkspaceIntent: CallbackAction<_RefreshWorkspaceIntent>(onInvoke: (_) {
            unawaited(_refreshOverview(selectFirstProject: false));
            unawaited(_refreshCommandCentre());
            if (_destination == _Destination.assistant || _destination == _Destination.settings || _destination == _Destination.health) {
              unawaited(_refreshAiWorkspace());
            }
            return null;
          }),
        },
        child: Scaffold(
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
        ),
      ),
    );
  }
}
