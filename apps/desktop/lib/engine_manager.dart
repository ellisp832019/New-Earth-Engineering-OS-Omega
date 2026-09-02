import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:flutter/foundation.dart';

import 'neos_client.dart';

enum EngineLifecycleState {
  notStarted,
  starting,
  waitingForHealth,
  connected,
  degraded,
  failed,
  stopping,
  stopped,
}

class DesktopSettings {
  const DesktopSettings({
    required this.dataDirectory,
    required this.serviceHost,
    required this.servicePort,
    required this.autoRefresh,
    required this.preferBundledBackend,
    required this.recentProjectId,
  });

  factory DesktopSettings.defaults() {
    return DesktopSettings(
      dataDirectory: _defaultDataDirectory(),
      serviceHost: '127.0.0.1',
      servicePort: 8765,
      autoRefresh: true,
      preferBundledBackend: true,
      recentProjectId: null,
    );
  }

  factory DesktopSettings.fromJson(Map<String, dynamic> json) {
    final defaults = DesktopSettings.defaults();
    return DesktopSettings(
      dataDirectory: _string(json['data_directory'], defaults.dataDirectory),
      serviceHost: _string(json['service_host'], defaults.serviceHost),
      servicePort: _int(json['service_port'], defaults.servicePort),
      autoRefresh: _bool(json['auto_refresh'], defaults.autoRefresh),
      preferBundledBackend: _bool(
        json['prefer_bundled_backend'],
        defaults.preferBundledBackend,
      ),
      recentProjectId: json['recent_project_id']?.toString(),
    );
  }

  final String dataDirectory;
  final String serviceHost;
  final int servicePort;
  final bool autoRefresh;
  final bool preferBundledBackend;
  final String? recentProjectId;

  DesktopSettings copyWith({
    String? dataDirectory,
    String? serviceHost,
    int? servicePort,
    bool? autoRefresh,
    bool? preferBundledBackend,
    String? recentProjectId,
  }) {
    return DesktopSettings(
      dataDirectory: dataDirectory ?? this.dataDirectory,
      serviceHost: serviceHost ?? this.serviceHost,
      servicePort: servicePort ?? this.servicePort,
      autoRefresh: autoRefresh ?? this.autoRefresh,
      preferBundledBackend: preferBundledBackend ?? this.preferBundledBackend,
      recentProjectId: recentProjectId ?? this.recentProjectId,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'data_directory': dataDirectory,
      'service_host': serviceHost,
      'service_port': servicePort,
      'auto_refresh': autoRefresh,
      'prefer_bundled_backend': preferBundledBackend,
      'recent_project_id': recentProjectId,
    };
  }
}

class EngineSnapshot {
  const EngineSnapshot({
    required this.state,
    required this.message,
    required this.serviceUri,
    required this.ownedBackend,
    required this.processId,
    required this.instanceId,
    required this.shutdownToken,
    required this.startedAt,
    required this.connectedAt,
    required this.health,
    required this.error,
  });

  factory EngineSnapshot.initial() {
    return const EngineSnapshot(
      state: EngineLifecycleState.notStarted,
      message: 'Starting up...',
      serviceUri: null,
      ownedBackend: false,
      processId: null,
      instanceId: null,
      shutdownToken: null,
      startedAt: null,
      connectedAt: null,
      health: null,
      error: null,
    );
  }

  final EngineLifecycleState state;
  final String message;
  final Uri? serviceUri;
  final bool ownedBackend;
  final int? processId;
  final String? instanceId;
  final String? shutdownToken;
  final DateTime? startedAt;
  final DateTime? connectedAt;
  final ServiceHealthInfo? health;
  final String? error;

  bool get isConnected => state == EngineLifecycleState.connected;
  bool get isOwned => ownedBackend && processId != null;

  EngineSnapshot copyWith({
    EngineLifecycleState? state,
    String? message,
    Uri? serviceUri,
    bool? ownedBackend,
    int? processId,
    String? instanceId,
    String? shutdownToken,
    DateTime? startedAt,
    DateTime? connectedAt,
    ServiceHealthInfo? health,
    String? error,
  }) {
    return EngineSnapshot(
      state: state ?? this.state,
      message: message ?? this.message,
      serviceUri: serviceUri ?? this.serviceUri,
      ownedBackend: ownedBackend ?? this.ownedBackend,
      processId: processId ?? this.processId,
      instanceId: instanceId ?? this.instanceId,
      shutdownToken: shutdownToken ?? this.shutdownToken,
      startedAt: startedAt ?? this.startedAt,
      connectedAt: connectedAt ?? this.connectedAt,
      health: health ?? this.health,
      error: error ?? this.error,
    );
  }
}

class NeosEngineManager {
  NeosEngineManager({HttpNeosClient? client, DesktopSettings? settings})
    : client = client ?? HttpNeosClient(),
      settings = settings ?? DesktopSettings.defaults();

  final HttpNeosClient client;
  DesktopSettings settings;
  final ValueNotifier<EngineSnapshot> snapshot = ValueNotifier(
    EngineSnapshot.initial(),
  );

  Process? _process;
  StreamSubscription<String>? _backendStdoutSub;
  StreamSubscription<String>? _backendStderrSub;
  Future<Uri>? _bootstrapFuture;
  Future<bool>? _shutdownFuture;
  Uri? _serviceUri;
  String? _shutdownToken;
  String? _lastStartupFailure;
  Uri? get serviceUri => _serviceUri;
  bool get ownsBackend => snapshot.value.ownedBackend;

  File get _settingsFile =>
      File(_joinPath([settings.dataDirectory, 'desktop-settings.json']));
  File get _logFile =>
      File(_joinPath([settings.dataDirectory, 'logs', 'neos-desktop.log']));

  Future<void> loadSettings() async {
    final file = _settingsFile;
    if (!await file.exists()) {
      await file.parent.create(recursive: true);
      await file.writeAsString(jsonEncode(settings.toJson()));
      return;
    }
    try {
      final decoded = jsonDecode(await file.readAsString());
      if (decoded is Map) {
        settings = DesktopSettings.fromJson(
          decoded.map((key, value) => MapEntry(key.toString(), value)),
        );
      }
    } catch (_) {
      // Keep defaults when settings are unreadable.
    }
  }

  Future<void> saveSettings() async {
    await _settingsFile.parent.create(recursive: true);
    await _settingsFile.writeAsString(
      const JsonEncoder.withIndent('  ').convert(settings.toJson()),
    );
  }

  Future<Uri> bootstrap() {
    return _bootstrapFuture ??= _bootstrapInternal();
  }

  Future<Uri> _bootstrapInternal() async {
    _lastStartupFailure = null;
    await loadSettings();
    _emit(
      snapshot.value.copyWith(
        state: EngineLifecycleState.starting,
        message: 'Checking local NEOS service...',
      ),
    );
    _log(
      'Checking local NEOS service at ${settings.serviceHost}:${settings.servicePort}',
    );

    final configuredUri = Uri.parse(
      'http://${settings.serviceHost}:${settings.servicePort}',
    );
    final existing = await _probeHealthy(configuredUri);
    if (existing != null && existing.isNeos) {
      _serviceUri = configuredUri;
      _emit(
        snapshot.value.copyWith(
          state: EngineLifecycleState.connected,
          message: 'Connected to existing NEOS service.',
          serviceUri: configuredUri,
          ownedBackend: false,
          processId: existing.ownerPid,
          instanceId: existing.instanceId.isEmpty ? null : existing.instanceId,
          health: existing,
          connectedAt: DateTime.now().toUtc(),
          startedAt: DateTime.now().toUtc(),
        ),
      );
      _log('Attached to existing NEOS service at $configuredUri');
      return configuredUri;
    }

    _emit(
      snapshot.value.copyWith(
        state: EngineLifecycleState.waitingForHealth,
        message: 'Starting local NEOS backend...',
      ),
    );
    final launch = await _launchBackend();
    if (launch == null) {
      final message = _lastStartupFailure ?? 'Unable to start NEOS backend.';
      _emit(
        snapshot.value.copyWith(
          state: EngineLifecycleState.failed,
          message: message,
          error: message,
        ),
      );
      throw StateError(message);
    }
    _process = launch.$1;
    _shutdownToken = launch.$2;
    _serviceUri = launch.$3;
    final ready = await _waitForHealthy(_serviceUri!);
    if (ready == null || !ready.isNeos) {
      final message = 'NEOS backend did not become healthy.';
      _lastStartupFailure ??= message;
      _emit(
        snapshot.value.copyWith(
          state: EngineLifecycleState.failed,
          message: message,
          error: message,
        ),
      );
      throw StateError(message);
    }
    _emit(
      snapshot.value.copyWith(
        state: EngineLifecycleState.connected,
        message: 'NEOS backend ready.',
        serviceUri: _serviceUri,
        ownedBackend: true,
        processId: _process?.pid,
        instanceId: ready.instanceId.isEmpty ? null : ready.instanceId,
        health: ready,
        connectedAt: DateTime.now().toUtc(),
        startedAt: DateTime.now().toUtc(),
      ),
    );
    _log(
      'Started owned NEOS backend at $_serviceUri with pid=${_process?.pid}',
    );
    settings = settings.copyWith(servicePort: _serviceUri!.port);
    await saveSettings();
    return _serviceUri!;
  }

  Future<void> reconnect() async {
    _bootstrapFuture = null;
    await bootstrap();
  }

  Future<bool> shutdownOwnedEngine() {
    return _shutdownFuture ??= _shutdownOwnedEngineInternal().whenComplete(() {
      _shutdownFuture = null;
    });
  }

  Future<void> shutdown() async {
    await shutdownOwnedEngine();
  }

  Future<bool> _shutdownOwnedEngineInternal() async {
    if (_process == null && _serviceUri == null) {
      _log('Shutdown requested but no backend or service URI is active.');
      return false;
    }
    _emit(
      snapshot.value.copyWith(
        state: EngineLifecycleState.stopping,
        message: 'Stopping backend...',
      ),
    );
    final owned =
        snapshot.value.ownedBackend &&
        _serviceUri != null &&
        _shutdownToken != null &&
        _process != null;
    if (owned) {
      try {
        final response = await client.shutdownService(
          _serviceUri!,
          _shutdownToken!,
        );
        _log('Controlled shutdown request acknowledged: $response');
      } catch (error) {
        _log('Controlled shutdown request failed: $error');
      }
      try {
        await _process!.exitCode.timeout(const Duration(seconds: 8));
        _log('Owned backend process exited after controlled shutdown.');
      } catch (_) {
        _log(
          'Owned backend did not exit in time; terminating specific PID ${_process?.pid}.',
        );
        _process?.kill(ProcessSignal.sigterm);
        try {
          await _process!.exitCode.timeout(const Duration(seconds: 5));
        } catch (error) {
          _log('Owned backend still running after terminate signal: $error');
        }
      }
    }
    final ownedShutdown = owned;
    await _backendStdoutSub?.cancel();
    await _backendStderrSub?.cancel();
    _backendStdoutSub = null;
    _backendStderrSub = null;
    _process = null;
    _serviceUri = null;
    _shutdownToken = null;
    _emit(
      snapshot.value.copyWith(
        state: EngineLifecycleState.stopped,
        message: 'Stopped.',
        ownedBackend: false,
        processId: null,
      ),
    );
    _log('Backend stopped.');
    return ownedShutdown;
  }

  Future<ServiceHealthInfo?> _probeHealthy(Uri baseUri) async {
    try {
      final health = await client.probeHealth(baseUri);
      return health.isNeos ? health : null;
    } catch (error) {
      _log('Probe failed at $baseUri: $error');
      return null;
    }
  }

  Future<ServiceHealthInfo?> _waitForHealthy(Uri baseUri) async {
    final deadline = DateTime.now().toUtc().add(const Duration(seconds: 30));
    while (DateTime.now().toUtc().isBefore(deadline)) {
      final health = await _probeHealthy(baseUri);
      if (health != null) {
        return health;
      }
      await Future<void>.delayed(const Duration(milliseconds: 250));
    }
    return null;
  }

  Future<(Process, String, Uri)?> _launchBackend() async {
    final instanceId = _randomId();
    final shutdownToken = _randomId();
    final dbPath = _settingsDbPath();
    final servicePort = settings.servicePort;
    final expectedUri = Uri.parse(
      'http://${settings.serviceHost}:$servicePort',
    );
    await File(dbPath).parent.create(recursive: true);
    final args = <String>[
      '-m',
      'neos',
      'service',
      'start',
      '--db',
      dbPath,
      '--host',
      settings.serviceHost,
      '--port',
      servicePort.toString(),
      '--instance-id',
      instanceId,
      '--owner-pid',
      pid.toString(),
      '--shutdown-token',
      shutdownToken,
    ];

    final bundled = _bundledBackendExecutable();
    Process process;
    if (bundled != null) {
      _log('Launching bundled backend: ${bundled.path}');
      process = await Process.start(
        bundled.path,
        [
          'service',
          'start',
          '--db',
          dbPath,
          '--host',
          settings.serviceHost,
          '--port',
          servicePort.toString(),
          '--instance-id',
          instanceId,
          '--owner-pid',
          pid.toString(),
          '--shutdown-token',
          shutdownToken,
        ],
        mode: ProcessStartMode.detachedWithStdio,
        workingDirectory: _packageRoot().path,
      );
    } else {
      final python = _pythonExecutable();
      _log('Launching python backend: $python ${args.join(' ')}');
      process = await Process.start(
        python,
        args,
        mode: ProcessStartMode.detachedWithStdio,
        workingDirectory: _repoRoot().path,
      );
    }
    final ready = await _waitForBackendReady(process, expectedUri);
    if (ready == null) {
      _lastStartupFailure ??= 'NEOS backend did not become healthy.';
      process.kill();
      return null;
    }
    return (process, shutdownToken, ready);
  }

  Future<Uri?> _waitForBackendReady(Process process, Uri expectedUri) async {
    // CR-04C1F: keep backend stdio drained for the process lifetime.
    //
    // ProcessStartMode.detachedWithStdio gives the desktop live pipes to the
    // child. Cancelling those subscriptions as soon as /health first passes
    // can close the pipes while the backend is still running. Keep them
    // attached until the owned process exits or is deliberately shut down.
    final stdoutLines = process.stdout
        .transform(utf8.decoder)
        .transform(const LineSplitter());
    final stderrLines = process.stderr
        .transform(utf8.decoder)
        .transform(const LineSplitter());

    await _backendStdoutSub?.cancel();
    await _backendStderrSub?.cancel();

    _backendStdoutSub = stdoutLines.listen((line) {
      _log('backend: $line');
    });
    _backendStderrSub = stderrLines.listen((line) => _log('backend: $line'));

    int? exitCode;
    process.exitCode.then((code) async {
      _log('backend exited with code $code');
      exitCode = code;
      await _backendStdoutSub?.cancel();
      await _backendStderrSub?.cancel();
      _backendStdoutSub = null;
      _backendStderrSub = null;
    });

    final deadline = DateTime.now().toUtc().add(const Duration(seconds: 30));
    try {
      while (DateTime.now().toUtc().isBefore(deadline)) {
        final health = await _probeHealthy(expectedUri);
        if (health != null) {
          return expectedUri;
        }
        if (exitCode != null) {
          _lastStartupFailure ??=
              'NEOS backend exited with code $exitCode before becoming healthy on $expectedUri.';
          return null;
        }
        await Future<void>.delayed(const Duration(milliseconds: 250));
      }
      if (exitCode != null) {
        _lastStartupFailure ??=
            'NEOS backend exited with code $exitCode before becoming healthy on $expectedUri.';
      } else {
        _lastStartupFailure ??=
            'NEOS backend did not become healthy on $expectedUri within 30 seconds.';
      }
      return null;
    } catch (error) {
      _lastStartupFailure ??= 'NEOS backend startup failed: $error';
      return null;
    }
  }

  String _settingsDbPath() {
    return _joinPath([settings.dataDirectory, 'neos.db']);
  }

  String _pythonExecutable() {
    return Platform.environment['NEOS_PYTHON'] ?? 'python';
  }

  File? _bundledBackendExecutable() {
    final candidates = <String>[
      _joinPath([_packageRoot().path, 'runtime', 'neos_engine.exe']),
      _joinPath([_packageRoot().path, 'neos_engine.exe']),
    ];
    for (final path in candidates) {
      final file = File(path);
      if (file.existsSync()) {
        return file;
      }
    }
    return null;
  }

  Directory _packageRoot() {
    return File(Platform.resolvedExecutable).absolute.parent;
  }

  Directory _repoRoot() {
    var current = Directory.current.absolute;
    for (var i = 0; i < 5; i++) {
      if (File(
        _joinPath([current.path, 'src', 'neos', 'cli.py']),
      ).existsSync()) {
        return current;
      }
      final parent = current.parent;
      if (parent.path == current.path) {
        break;
      }
      current = parent;
    }
    return Directory.current.absolute;
  }

  void _emit(EngineSnapshot next) {
    snapshot.value = next;
    _log('[${next.state.name}] ${next.message}');
  }

  void _log(String line) {
    final timestamp = DateTime.now().toUtc().toIso8601String();
    unawaited(_appendLogLine('$timestamp $line'));
  }

  Future<void> _appendLogLine(String line) async {
    await _logFile.parent.create(recursive: true);
    await _logFile.writeAsString('$line\n', mode: FileMode.append);
  }

  static String _joinPath(List<String> parts) {
    return parts.join(Platform.pathSeparator);
  }

  static String _randomId() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    return base64Url.encode(bytes).replaceAll('=', '');
  }
}

String _defaultDataDirectory() {
  final localAppData = Platform.environment['LOCALAPPDATA'];
  if (localAppData != null && localAppData.isNotEmpty) {
    return '$localAppData${Platform.pathSeparator}New Earth Engineering OS';
  }
  final home = Platform.environment['HOME'] ?? Directory.current.path;
  return '$home${Platform.pathSeparator}.neos-desktop';
}

String _string(dynamic value, [String fallback = '']) =>
    value == null ? fallback : value.toString();
int _int(dynamic value, [int fallback = 0]) =>
    value is int ? value : int.tryParse(_string(value)) ?? fallback;
bool _bool(dynamic value, bool fallback) => value is bool ? value : fallback;
