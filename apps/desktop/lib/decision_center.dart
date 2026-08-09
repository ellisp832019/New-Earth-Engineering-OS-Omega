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

class DecisionCentre extends StatefulWidget {
  const DecisionCentre({
    super.key,
    required this.client,
    required this.serviceUri,
    this.selectedProjectId,
  });

  final NeosClient client;
  final Uri serviceUri;
  final String? selectedProjectId;

  @override
  State<DecisionCentre> createState() => _DecisionCentreState();
}

class _DecisionCentreState extends State<DecisionCentre> {
  final TextEditingController _titleController = TextEditingController(text: 'What should we do next?');
  final TextEditingController _descriptionController = TextEditingController(text: 'Evaluate the portfolio evidence and propose the next deterministic action.');
  final TextEditingController _decisionTypeController = TextEditingController(text: 'engineering_next_action');
  final TextEditingController _compareQuestionController = TextEditingController(text: 'Compare these architecture options.');
  final TextEditingController _compareDecisionTypeController = TextEditingController(text: 'architecture');
  final TextEditingController _optionsController = TextEditingController(
    text: jsonEncode([
      {'name': 'Option A', 'description': 'Keep current architecture.'},
      {'name': 'Option B', 'description': 'Introduce a shared module.'},
      {'name': 'Option C', 'description': 'Defer and gather more evidence.'},
    ]),
  );
  final TextEditingController _scenarioController = TextEditingController(
    text: jsonEncode({
      'title': 'Add a shared platform module',
      'change': 'Consolidate duplicated logic into a shared module.',
      'affected_entities': const ['architecture', 'reuse', 'tests'],
    }),
  );

  bool _loading = true;
  bool _running = false;
  String? _error;
  Map<String, dynamic>? _inbox;
  Map<String, dynamic>? _nextActions;
  Map<String, dynamic>? _releaseReadiness;
  Map<String, dynamic>? _reuse;
  Map<String, dynamic>? _testPriorities;
  Map<String, dynamic>? _debtPriorities;
  Map<String, dynamic>? _history;
  Map<String, dynamic>? _recommendation;
  Map<String, dynamic>? _comparison;
  Map<String, dynamic>? _scenario;

  List<String> get _scope => widget.selectedProjectId == null || widget.selectedProjectId!.isEmpty ? const <String>[] : <String>[widget.selectedProjectId!];

  @override
  void initState() {
    super.initState();
    unawaited(_refresh());
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _decisionTypeController.dispose();
    _compareQuestionController.dispose();
    _compareDecisionTypeController.dispose();
    _optionsController.dispose();
    _scenarioController.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final futures = <Future<Map<String, dynamic>>>[
        widget.client.loadDecisionInbox(widget.serviceUri, projectIds: _scope.isEmpty ? null : _scope),
        widget.client.loadDecisionNextActions(widget.serviceUri, projectIds: _scope.isEmpty ? null : _scope),
        widget.client.loadDecisionReuse(widget.serviceUri, projectIds: _scope.isEmpty ? null : _scope),
        widget.client.loadDecisionTestPriorities(widget.serviceUri, projectIds: _scope.isEmpty ? null : _scope),
        widget.client.loadDecisionDebtPriorities(widget.serviceUri, projectIds: _scope.isEmpty ? null : _scope),
        widget.client.loadDecisionHistory(widget.serviceUri, projectIds: _scope.isEmpty ? null : _scope),
      ];
      if (widget.selectedProjectId != null && widget.selectedProjectId!.isNotEmpty) {
        futures.insert(2, widget.client.loadDecisionReleaseReadiness(widget.serviceUri, widget.selectedProjectId!));
      }
      final results = await Future.wait(futures);
      setState(() {
        _inbox = results[0];
        _nextActions = results[1];
        if (widget.selectedProjectId != null && widget.selectedProjectId!.isNotEmpty) {
          _releaseReadiness = results[2];
          _reuse = results[3];
          _testPriorities = results[4];
          _debtPriorities = results[5];
          _history = results[6];
        } else {
          _releaseReadiness = null;
          _reuse = results[2];
          _testPriorities = results[3];
          _debtPriorities = results[4];
          _history = results[5];
        }
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _loading = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _evaluate() async {
    final title = _titleController.text.trim();
    final description = _descriptionController.text.trim();
    final decisionType = _decisionTypeController.text.trim();
    if (title.isEmpty || decisionType.isEmpty) {
      setState(() {
        _error = 'Enter a title and decision type first.';
      });
      return;
    }
    setState(() {
      _running = true;
      _error = null;
    });
    try {
      final payload = <String, dynamic>{
        'title': title,
        'description': description,
        'decision_type': decisionType,
        'scope': _scope.isEmpty ? 'portfolio' : 'project',
        if (_scope.isNotEmpty) 'project_ids': _scope,
      };
      final response = await widget.client.evaluateDecision(widget.serviceUri, payload);
      setState(() {
        _recommendation = response;
        _running = false;
      });
      await _refresh();
    } catch (error) {
      setState(() {
        _running = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _compare() async {
    final question = _compareQuestionController.text.trim();
    final decisionType = _compareDecisionTypeController.text.trim();
    if (question.isEmpty || decisionType.isEmpty) {
      setState(() {
        _error = 'Enter a comparison question and decision type first.';
      });
      return;
    }
    List<dynamic> parsedOptions;
    try {
      parsedOptions = _list(jsonDecode(_optionsController.text));
    } catch (error) {
      setState(() {
        _error = 'Options must be valid JSON: $error';
      });
      return;
    }
    setState(() {
      _running = true;
      _error = null;
    });
    try {
      final response = await widget.client.compareDecisionOptions(widget.serviceUri, {
        'question': question,
        'decision_type': decisionType,
        'options': parsedOptions,
        if (_scope.isNotEmpty) 'project_ids': _scope,
      });
      setState(() {
        _comparison = response;
        _running = false;
      });
      await _refresh();
    } catch (error) {
      setState(() {
        _running = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _scenarioRun() async {
    try {
      final payload = _map(jsonDecode(_scenarioController.text));
      setState(() {
        _running = true;
        _error = null;
      });
      final response = await widget.client.runDecisionScenario(widget.serviceUri, payload, projectIds: _scope.isEmpty ? null : _scope);
      setState(() {
        _scenario = response;
        _running = false;
      });
      await _refresh();
    } catch (error) {
      setState(() {
        _running = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _markDecision(String questionId, Future<Map<String, dynamic>> Function() action) async {
    setState(() {
      _running = true;
      _error = null;
    });
    try {
      await action();
      setState(() {
        _running = false;
      });
      await _refresh();
    } catch (error) {
      setState(() {
        _running = false;
        _error = error.toString();
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

  Widget _panel({required String title, String? subtitle, required Widget child}) {
    return Card(
      elevation: 0,
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            if (subtitle != null) ...[
              const SizedBox(height: 4),
              Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.black54)),
            ],
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
      child: SelectableText(_prettyJson(data), style: const TextStyle(fontFamily: 'Consolas', fontSize: 12)),
    );
  }

  Widget _metricCard(String title, String value, String subtitle, IconData icon) {
    return Card(
      elevation: 0,
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: const Color(0xFF1D4ED8)),
            const SizedBox(height: 12),
            Text(title, style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 4),
            Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.black54)),
          ],
        ),
      ),
    );
  }

  Widget _decisionItem(Map<String, dynamic> item) {
    final question = _map(item['question']);
    final recommendation = _map(item['recommendation']);
    final review = _map(item['review']);
    final questionId = _string(question['id']);
    return Card(
      elevation: 0,
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(_string(question['title'], questionId), style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                ),
                Chip(label: Text(_string(question['status'], 'draft'))),
              ],
            ),
            const SizedBox(height: 8),
            Text(_string(question['description'])),
            const SizedBox(height: 10),
            Text('Recommended: ${_string(recommendation['recommended_option'], 'pending')}'),
            Text('Strength: ${_string(recommendation['strength'], 'unknown')}'),
            if (_string(review['review_state']).isNotEmpty) Text('Review: ${_string(review['review_state'])}'),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton(
                  onPressed: _running ? null : () => _markDecision(questionId, () => widget.client.acceptDecision(widget.serviceUri, questionId, selectedOption: _string(recommendation['recommended_option']))),
                  child: const Text('Accept'),
                ),
                OutlinedButton(
                  onPressed: _running ? null : () => _markDecision(questionId, () => widget.client.rejectDecision(widget.serviceUri, questionId, selectedOption: _string(recommendation['recommended_option']))),
                  child: const Text('Reject'),
                ),
                OutlinedButton(
                  onPressed: _running ? null : () => _markDecision(questionId, () => widget.client.deferDecision(widget.serviceUri, questionId, selectedOption: _string(recommendation['recommended_option']))),
                  child: const Text('Defer'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _tabBody(String title, Map<String, dynamic>? data, {String? subtitle}) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _panel(
            title: title,
            subtitle: subtitle,
            child: Text(
              widget.selectedProjectId == null || widget.selectedProjectId!.isEmpty
                  ? 'Portfolio scope selected. This view is deterministic and read-only until you accept, reject, or defer a recommendation.'
                  : 'Project scope: ${widget.selectedProjectId}.',
            ),
          ),
          const SizedBox(height: 16),
          _jsonPanel(title, data),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final inboxItems = _list(_map(_inbox)['items']).map((item) => _map(item)).toList(growable: false);
    final inboxCount = _map(_inbox)['count']?.toString() ?? '0';
    final nextCount = _list(_map(_nextActions)['items']).length.toString();
    final historyCount = _map(_history)['count']?.toString() ?? '0';
    final reuseData = _map(_reuse);
    final reuseCount = reuseData['candidates'] != null ? _list(reuseData['candidates']).length.toString() : reuseData['count']?.toString() ?? '0';
    return DefaultTabController(
      length: 8,
      child: Scaffold(
        body: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFFF8FAFC), Color(0xFFE2E8F0), Color(0xFFF8FAFC)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Decision Centre', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
                            const SizedBox(height: 4),
                            Text('Deterministic recommendation engine, inbox and operator review workflow.', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.black54)),
                          ],
                        ),
                      ),
                      FilledButton.icon(
                        onPressed: _loading ? null : _refresh,
                        icon: const Icon(Icons.refresh),
                        label: Text(_loading ? 'Loading...' : 'Refresh'),
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Row(
                    children: [
                      Expanded(child: _metricCard('Inbox', inboxCount, 'Pending or draft decision questions', Icons.inbox_outlined)),
                      const SizedBox(width: 12),
                      Expanded(child: _metricCard('Next actions', nextCount, 'Deterministic prioritisation output', Icons.route_outlined)),
                      const SizedBox(width: 12),
                      Expanded(child: _metricCard('Reuse', reuseCount, 'Cross-project reuse candidates', Icons.share_outlined)),
                      const SizedBox(width: 12),
                      Expanded(child: _metricCard('History', historyCount, 'Recorded decision evaluations', Icons.history_outlined)),
                    ],
                  ),
                ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.all(20),
                    child: _panel(
                      title: 'Error',
                      child: Text(_error!, style: const TextStyle(color: Colors.redAccent)),
                    ),
                  ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: TabBar(
                    isScrollable: true,
                    tabs: const [
                      Tab(text: 'Inbox'),
                      Tab(text: 'Recommendations'),
                      Tab(text: 'Next Actions'),
                      Tab(text: 'Release Readiness'),
                      Tab(text: 'Reuse'),
                      Tab(text: 'Reviews'),
                      Tab(text: 'Scenario'),
                      Tab(text: 'History'),
                    ],
                  ),
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _panel(
                              title: 'Inbox',
                              subtitle: 'Pending decision questions that are ready for operator review.',
                              child: Text(
                                inboxItems.isEmpty
                                    ? 'No pending decision questions are available right now.'
                                    : 'Review each question and choose whether to accept, reject, or defer the deterministic recommendation.',
                              ),
                            ),
                            const SizedBox(height: 16),
                            if (inboxItems.isEmpty)
                              _jsonPanel('Inbox payload', _inbox, subtitle: 'The raw inbox response.'),
                            for (final item in inboxItems) ...[
                              _decisionItem(item),
                              const SizedBox(height: 12),
                            ],
                          ],
                        ),
                      ),
                      SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _panel(
                              title: 'Evaluate decision',
                              subtitle: 'This always runs the deterministic engine. It does not call the AI assistant.',
                              child: Column(
                                children: [
                                  TextField(controller: _titleController, decoration: const InputDecoration(labelText: 'Title')),
                                  const SizedBox(height: 12),
                                  TextField(controller: _descriptionController, decoration: const InputDecoration(labelText: 'Description'), maxLines: 3),
                                  const SizedBox(height: 12),
                                  TextField(controller: _decisionTypeController, decoration: const InputDecoration(labelText: 'Decision type')),
                                  const SizedBox(height: 12),
                                  Align(
                                    alignment: Alignment.centerLeft,
                                    child: FilledButton(
                                      onPressed: _running ? null : _evaluate,
                                      child: Text(_running ? 'Evaluating...' : 'Evaluate'),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                            _jsonPanel('Latest recommendation', _recommendation, subtitle: 'Operator-reviewed deterministic recommendation.'),
                            const SizedBox(height: 16),
                            _panel(
                              title: 'Compare options',
                              subtitle: 'Paste a JSON array of candidate options and evaluate them against the current portfolio evidence.',
                              child: Column(
                                children: [
                                  TextField(controller: _compareQuestionController, decoration: const InputDecoration(labelText: 'Question')),
                                  const SizedBox(height: 12),
                                  TextField(controller: _compareDecisionTypeController, decoration: const InputDecoration(labelText: 'Decision type')),
                                  const SizedBox(height: 12),
                                  TextField(controller: _optionsController, decoration: const InputDecoration(labelText: 'Options JSON'), minLines: 6, maxLines: 10),
                                  const SizedBox(height: 12),
                                  Align(
                                    alignment: Alignment.centerLeft,
                                    child: FilledButton(
                                      onPressed: _running ? null : _compare,
                                      child: Text(_running ? 'Comparing...' : 'Compare'),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                            _jsonPanel('Comparison result', _comparison, subtitle: 'Deterministic ranking of the supplied options.'),
                          ],
                        ),
                      ),
                      _tabBody('Next actions', _nextActions, subtitle: 'Ordered next steps derived from portfolio evidence.'),
                      _tabBody('Release readiness', _releaseReadiness, subtitle: 'Project gate analysis for the selected project.'),
                      _tabBody('Reuse', _reuse, subtitle: 'Candidates for deterministic cross-project reuse.'),
                      _tabBody(
                        'Reviews',
                        {
                          'project_scope': _scope,
                          'test_priorities': _testPriorities,
                          'debt_priorities': _debtPriorities,
                        },
                        subtitle: 'Priority reviews for tests and technical debt.',
                      ),
                      SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _panel(
                              title: 'Scenario analysis',
                              subtitle: 'Describe a change and inspect expected impacts before making it real.',
                              child: Column(
                                children: [
                                  TextField(controller: _scenarioController, decoration: const InputDecoration(labelText: 'Scenario JSON'), minLines: 6, maxLines: 12),
                                  const SizedBox(height: 12),
                                  Align(
                                    alignment: Alignment.centerLeft,
                                    child: FilledButton(
                                      onPressed: _running ? null : _scenarioRun,
                                      child: Text(_running ? 'Running...' : 'Run scenario'),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                            _jsonPanel('Scenario result', _scenario, subtitle: 'Expected effects, gaps and review surfaces.'),
                          ],
                        ),
                      ),
                      SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: _jsonPanel('Decision history', _history, subtitle: 'All deterministic evaluations and operator reviews.'),
                      ),
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
