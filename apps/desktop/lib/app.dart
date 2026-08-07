import 'dart:convert';

import 'package:flutter/material.dart';

import 'neos_client.dart';

enum _Destination {
  home,
  projects,
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

  _Destination _destination = _Destination.home;
  ServiceOverview? _overview;
  ProjectRecord? _project;
  String? _selectedProjectId;
  String? _error;
  bool _loadingOverview = true;
  bool _loadingProject = false;

  static const List<_NavItem> _items = <_NavItem>[
    _NavItem(_Destination.home, Icons.home_outlined, 'Home'),
    _NavItem(_Destination.projects, Icons.folder_outlined, 'Projects'),
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
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: 'AI Engineering Assistant',
            subtitle: 'The desktop shell stays deterministic and exposes evidence. Interpretation happens above the core, not inside widgets.',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                _Bullet(text: 'Ask questions against the current project and cite the evidence payload directly.'),
                _Bullet(text: 'Use freshness, scope and uncertainty panels before trusting any generated answer.'),
                _Bullet(text: 'Keep model output separate from canonical service responses.'),
                _Bullet(text: 'If you add a generated response layer later, it should consume these same local service endpoints.'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel('Evidence focus', project?.summary ?? const {}, subtitle: 'The selected project summary is the first place to verify before answering questions.'),
          const SizedBox(height: 16),
          _panel(
            title: 'Sample prompt',
            subtitle: 'A simple prompt pattern this UI is prepared to support later.',
            child: SelectableText(
              'What changed in ${project?.projectId ?? 'this project'} recently, and which evidence items support that answer?',
            ),
          ),
        ],
      ),
    );
  }

  Widget _settingsView() {
    final overview = _overview;
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
          _jsonPanel('Service health', overview?.health, subtitle: 'Raw backend health payload.'),
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
