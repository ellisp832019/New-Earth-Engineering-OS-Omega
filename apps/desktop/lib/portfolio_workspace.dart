import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';

import 'neos_client.dart';

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

class PortfolioWorkspace extends StatefulWidget {
  const PortfolioWorkspace({
    super.key,
    required this.client,
    required this.serviceUri,
    this.selectedProjectId,
  });

  final NeosClient client;
  final Uri serviceUri;
  final String? selectedProjectId;

  @override
  State<PortfolioWorkspace> createState() => _PortfolioWorkspaceState();
}

class _PortfolioWorkspaceState extends State<PortfolioWorkspace> {
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _questionController = TextEditingController(text: 'What should the portfolio prioritise next?');

  bool _loading = true;
  bool _searching = false;
  bool _askingAi = false;
  String? _error;
  Map<String, dynamic>? _ecosystem;
  Map<String, dynamic>? _projects;
  Map<String, dynamic>? _capabilities;
  Map<String, dynamic>? _technologies;
  Map<String, dynamic>? _reuse;
  Map<String, dynamic>? _duplication;
  Map<String, dynamic>? _dependencies;
  Map<String, dynamic>? _risks;
  Map<String, dynamic>? _unknowns;
  Map<String, dynamic>? _attention;
  Map<String, dynamic>? _timeline;
  Map<String, dynamic>? _searchResults;
  Map<String, dynamic>? _aiResponse;
  List<Map<String, dynamic>> _aiCitations = const [];
  final Set<String> _selectedProjectIds = <String>{};

  @override
  void initState() {
    super.initState();
    unawaited(_refresh());
  }

  @override
  void dispose() {
    _searchController.dispose();
    _questionController.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> get _projectItems => _list(_projects?['projects']).map((item) => _map(item)).toList(growable: false);

  List<String> get _selectedScope {
    if (_selectedProjectIds.isNotEmpty) {
      return _selectedProjectIds.toList(growable: false);
    }
    final selected = widget.selectedProjectId;
    if (selected != null && selected.isNotEmpty) {
      return <String>[selected];
    }
    return _projectItems.map((item) => _string(item['project_id'])).where((value) => value.isNotEmpty).toList(growable: false);
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await Future.wait([
        widget.client.loadEcosystem(widget.serviceUri),
        widget.client.loadEcosystemProjects(widget.serviceUri),
        widget.client.loadEcosystemCapabilities(widget.serviceUri),
        widget.client.loadEcosystemTechnologies(widget.serviceUri),
        widget.client.loadEcosystemReuse(widget.serviceUri),
        widget.client.loadEcosystemDuplication(widget.serviceUri),
        widget.client.loadEcosystemDependencies(widget.serviceUri),
        widget.client.loadEcosystemRisks(widget.serviceUri),
        widget.client.loadEcosystemUnknowns(widget.serviceUri),
        widget.client.loadEcosystemAttention(widget.serviceUri),
        widget.client.loadEcosystemTimeline(widget.serviceUri),
      ]);
      final projects = _map(results[1]);
      final items = _list(projects['projects']).map((item) => _map(item)).toList(growable: false);
      final nextSelection = <String>{
        if (_selectedProjectIds.isNotEmpty) ..._selectedProjectIds,
        if (_selectedProjectIds.isEmpty && widget.selectedProjectId?.isNotEmpty == true) widget.selectedProjectId!,
        if (_selectedProjectIds.isEmpty && (widget.selectedProjectId?.isEmpty ?? true) && items.length == 1) _string(items.first['project_id']),
      };
      if (_selectedProjectIds.isEmpty && nextSelection.isEmpty) {
        nextSelection.addAll(items.map((item) => _string(item['project_id'])).where((value) => value.isNotEmpty));
      }
      setState(() {
        _ecosystem = _map(results[0]);
        _projects = projects;
        _capabilities = _map(results[2]);
        _technologies = _map(results[3]);
        _reuse = _map(results[4]);
        _duplication = _map(results[5]);
        _dependencies = _map(results[6]);
        _risks = _map(results[7]);
        _unknowns = _map(results[8]);
        _attention = _map(results[9]);
        _timeline = _map(results[10]);
        _selectedProjectIds
          ..clear()
          ..addAll(nextSelection);
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _loading = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _runSearch() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) {
      setState(() {
        _searchResults = <String, dynamic>{'query': '', 'count': 0, 'items': const []};
      });
      return;
    }
    setState(() {
      _searching = true;
      _error = null;
    });
    try {
      final result = await widget.client.searchEcosystem(
        widget.serviceUri,
        query,
        projectIds: _selectedScope,
        limit: 20,
        offset: 0,
      );
      setState(() {
        _searchResults = result;
        _searching = false;
      });
    } catch (error) {
      setState(() {
        _searching = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _askPortfolioAi() async {
    final question = _questionController.text.trim();
    if (question.isEmpty) {
      return;
    }
    final scope = _selectedScope;
    if (scope.isEmpty) {
      setState(() {
        _error = 'Select at least one project before asking portfolio AI.';
      });
      return;
    }
    setState(() {
      _askingAi = true;
      _error = null;
    });
    try {
      final response = await widget.client.askAi(
        widget.serviceUri,
        projectId: scope.length > 1 ? 'portfolio' : scope.first,
        projectIds: scope,
        question: question,
        mode: 'portfolio_review',
      );
      final requestId = _string(response['request_id']);
      final citations = requestId.isEmpty
          ? const <Map<String, dynamic>>[]
          : _list((await widget.client.loadAiRequestCitations(widget.serviceUri, requestId))['citations']).map((item) => _map(item)).toList(growable: false);
      setState(() {
        _aiResponse = response;
        _aiCitations = citations;
        _askingAi = false;
      });
    } catch (error) {
      setState(() {
        _askingAi = false;
        _error = error.toString();
      });
    }
  }

  void _toggleProject(String projectId, bool selected) {
    setState(() {
      if (selected) {
        _selectedProjectIds.add(projectId);
      } else {
        _selectedProjectIds.remove(projectId);
      }
    });
  }

  Widget _statCard(String label, String value, {IconData icon = Icons.data_thresholding_outlined}) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: const Color(0xFFE2E8F0),
              child: Icon(icon, color: const Color(0xFF0F766E)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: const TextStyle(fontSize: 12, color: Colors.black54)),
                  const SizedBox(height: 4),
                  Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sectionHeader(String title, String subtitle, {Widget? trailing}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              Text(subtitle, style: const TextStyle(color: Colors.black54)),
            ],
          ),
        ),
        trailing ?? const SizedBox.shrink(),
      ],
    );
  }

  Widget _jsonCard(String title, dynamic data, {String subtitle = ''}) {
    final text = const JsonEncoder.withIndent('  ').convert(data ?? <String, dynamic>{});
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _sectionHeader(title, subtitle),
            const SizedBox(height: 12),
            SelectableText(text, style: const TextStyle(fontFamily: 'Consolas', fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _listCard(String title, List<Map<String, dynamic>> items, {String subtitle = '', String emptyText = 'No results.'}) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _sectionHeader(title, subtitle),
            const SizedBox(height: 12),
            if (items.isEmpty)
              Text(emptyText, style: const TextStyle(color: Colors.black54))
            else
              ...items.map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.circle_outlined, size: 18),
                    title: Text(_string(item['title'], _string(item['name'], _string(item['id'], 'Item')))),
                    subtitle: Text(_string(item['summary'], _string(item['reason'], _string(item['description'], '')))),
                    trailing: Text(_string(item['score'])),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  List<Map<String, dynamic>> _capabilityItems() {
    return _list(_capabilities?['shared_capabilities']).map((item) => _map(item)).toList(growable: false);
  }

  List<Map<String, dynamic>> _technologyItems() {
    return _list(_technologies?['technologies']).map((item) => _map(item)).toList(growable: false);
  }

  List<Map<String, dynamic>> _searchItems() {
    return _list(_searchResults?['items']).map((item) => _map(item)).toList(growable: false);
  }

  List<Map<String, dynamic>> _countItems(Map<String, dynamic>? payload) {
    return _list(payload?['items']).map((item) => _map(item)).toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    final projectItems = _projectItems;
    final selectedScope = _selectedScope;
    final ecosystem = _ecosystem ?? const <String, dynamic>{};
    final health = _map(ecosystem['health']);
    return DefaultTabController(
      length: 12,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _sectionHeader(
                  'Portfolio Workspace',
                  'Cross-project intelligence, overlap detection, reuse opportunities, and portfolio AI scope.',
                  trailing: FilledButton.icon(
                    onPressed: _loading ? null : _refresh,
                    icon: const Icon(Icons.refresh),
                    label: Text(_loading ? 'Refreshing...' : 'Refresh'),
                  ),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    _statCard('Projects', _string(_projects?['count'], '${projectItems.length}'), icon: Icons.folder_outlined),
                    _statCard('Health', _string(health['score'], _string(ecosystem['health_score'], 'n/a')), icon: Icons.favorite_outline),
                    _statCard('Shared capabilities', '${_capabilityItems().length}', icon: Icons.schema_outlined),
                    _statCard('Reuse candidates', '${_int(_reuse?['count'])}', icon: Icons.recycling_outlined),
                    _statCard('Overlap findings', '${_int(_duplication?['count'])}', icon: Icons.copy_outlined),
                    _statCard('Portfolio risks', '${_int(_risks?['count'])}', icon: Icons.warning_amber_outlined),
                  ],
                ),
                const SizedBox(height: 12),
                if (_loading)
                  const LinearProgressIndicator(minHeight: 3)
                else if (_error != null)
                  Text(_error!, style: const TextStyle(color: Colors.redAccent)),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Align(
              alignment: Alignment.centerLeft,
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: TabBar(
                  isScrollable: true,
                  tabs: const [
                    Tab(text: 'Overview'),
                    Tab(text: 'Projects'),
                    Tab(text: 'Capabilities'),
                    Tab(text: 'Technologies'),
                    Tab(text: 'Reuse'),
                    Tab(text: 'Overlap'),
                    Tab(text: 'Dependencies'),
                    Tab(text: 'Risks'),
                    Tab(text: 'Attention'),
                    Tab(text: 'Timeline'),
                    Tab(text: 'Search'),
                    Tab(text: 'AI Portfolio'),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: TabBarView(
              children: [
                _overviewTab(health, projectItems, selectedScope),
                _projectsTab(projectItems),
                _listCard('Capability Matrix', _capabilityItems(), subtitle: 'Shared capabilities across the selected portfolio scope.', emptyText: 'No shared capabilities yet.'),
                _listCard('Technology Matrix', _technologyItems(), subtitle: 'Technology inventory grouped by project overlap.', emptyText: 'No technologies yet.'),
                _listCard('Reuse Workbench', _countItems(_reuse), subtitle: 'Candidates where one project can inform another.', emptyText: 'No reuse opportunities identified.'),
                _listCard('Overlap Intelligence', _countItems(_duplication), subtitle: 'Potential duplication and deliberate overlap signals.', emptyText: 'No overlap findings identified.'),
                _listCard('Dependencies', _countItems(_dependencies), subtitle: 'Cross-project dependency edges.', emptyText: 'No portfolio dependencies identified.'),
                _listCard('Portfolio Risks', _countItems(_risks), subtitle: 'Risk clusters emerging from the current portfolio state.', emptyText: 'No portfolio risks identified.'),
                _listCard('Attention', _countItems(_attention), subtitle: 'What deserves attention next.', emptyText: 'No attention items identified.'),
                _listCard('Timeline', _countItems(_timeline), subtitle: 'Portfolio timeline events and snapshots.', emptyText: 'No timeline events available.'),
                _searchTab(),
                _aiTab(projectItems, selectedScope),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _overviewTab(Map<String, dynamic> health, List<Map<String, dynamic>> projects, List<String> selectedScope) {
    final summaryChips = Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        Chip(label: Text('Selected scope: ${selectedScope.isEmpty ? 'none' : selectedScope.join(', ')}')),
        Chip(label: Text('Projects loaded: ${projects.length}')),
        Chip(label: Text('Unknowns: ${_int(_unknowns?['count'])}')),
        Chip(label: Text('Attention: ${_int(_attention?['count'])}')),
      ],
    );
    final notice = projects.length == 1
        ? 'Only one registered project is available. The portfolio view is still useful for deterministic single-project validation, but cross-project comparisons will remain limited until more projects are added.'
        : 'Multiple registered projects are available. Portfolio comparisons, reuse, overlap, and dependency views are now active.';
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _jsonCard('Portfolio health', health, subtitle: 'Deterministic aggregate health for the selected portfolio scope.'),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Scope', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                summaryChips,
                const SizedBox(height: 12),
                Text(notice),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _projectsTab(List<Map<String, dynamic>> projects) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _sectionHeader('Registered Projects', 'Select the projects that should feed portfolio AI and search.'),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: projects.map((project) {
            final projectId = _string(project['project_id']);
            final selected = _selectedScope.contains(projectId);
            return FilterChip(
              label: Text(projectId),
              selected: selected,
              onSelected: (value) => _toggleProject(projectId, value),
            );
          }).toList(growable: false),
        ),
        const SizedBox(height: 12),
        ...projects.map(
          (project) => Card(
            child: ListTile(
              title: Text(_string(project['display_name'], _string(project['project_id']))),
              subtitle: Text(
                '${_string(project['status'])} • ${_string(project['family'])} • ${_string(project['repository_type'])}',
              ),
              trailing: Text(_string(project['project_id'])),
            ),
          ),
        ),
      ],
    );
  }

  Widget _searchTab() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _sectionHeader('Ecosystem Search', 'Search across the selected portfolio scope for projects, capabilities, technologies, reuse, risks, and overlap.'),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _searchController,
                decoration: const InputDecoration(
                  labelText: 'Search query',
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (_) => unawaited(_runSearch()),
              ),
            ),
            const SizedBox(width: 12),
            FilledButton.icon(
              onPressed: _searching ? null : () => unawaited(_runSearch()),
              icon: const Icon(Icons.search),
              label: Text(_searching ? 'Searching...' : 'Search'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _listCard(
          'Search Results',
          _searchItems(),
          subtitle: 'Results ranked deterministically from the portfolio analysis.',
          emptyText: 'Run a search to see ranked ecosystem results.',
        ),
      ],
    );
  }

  Widget _aiTab(List<Map<String, dynamic>> projects, List<String> selectedScope) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _sectionHeader('AI Portfolio', 'Ask questions about multiple projects at once. Citations remain visible and each citation keeps its source project IDs in metadata.'),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: projects.map((project) {
            final projectId = _string(project['project_id']);
            return FilterChip(
              label: Text(projectId),
              selected: _selectedScope.contains(projectId),
              onSelected: (value) => _toggleProject(projectId, value),
            );
          }).toList(growable: false),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _questionController,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: 'Portfolio question',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            FilledButton.icon(
              onPressed: _askingAi ? null : () => unawaited(_askPortfolioAi()),
              icon: const Icon(Icons.psychology_outlined),
              label: Text(_askingAi ? 'Asking...' : 'Ask portfolio AI'),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                selectedScope.isEmpty
                    ? 'Select one or more projects to enable portfolio AI scope.'
                    : 'Portfolio AI scope: ${selectedScope.join(', ')}',
                style: const TextStyle(color: Colors.black54),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        _jsonCard('AI response', _aiResponse, subtitle: 'Deterministic AI response for the selected portfolio scope.'),
        const SizedBox(height: 12),
        _jsonCard('AI citations', {'count': _aiCitations.length, 'citations': _aiCitations}, subtitle: 'Citations preserve project metadata so multi-project answers stay auditable.'),
      ],
    );
  }
}
