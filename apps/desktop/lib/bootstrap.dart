import 'dart:async';
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app.dart';
import 'engine_manager.dart';

class NeosBootstrapApp extends StatefulWidget {
  const NeosBootstrapApp({super.key, required this.manager});

  final NeosEngineManager manager;

  @override
  State<NeosBootstrapApp> createState() => _NeosBootstrapAppState();
}

class _NeosBootstrapAppState extends State<NeosBootstrapApp> {
  late final AppLifecycleListener _lifecycleListener;
  late final MethodChannel _windowChannel = const MethodChannel('neos/window');
  late Future<void> _bootstrap = _bootstrapWithAutoRetry();

  @override
  void initState() {
    super.initState();
    _lifecycleListener = AppLifecycleListener(
      onExitRequested: _handleExitRequested,
    );
    _windowChannel.setMethodCallHandler(_handleWindowMethodCall);
  }

  @override
  void dispose() {
    _windowChannel.setMethodCallHandler(null);
    _lifecycleListener.dispose();
    unawaited(widget.manager.shutdown());
    super.dispose();
  }

  Future<AppExitResponse> _handleExitRequested() async {
    await widget.manager.shutdownOwnedEngine();
    return AppExitResponse.exit;
  }

  Future<void> _handleWindowMethodCall(MethodCall call) async {
    switch (call.method) {
      case 'requestExit':
        await widget.manager.shutdownOwnedEngine();
        if (!mounted) {
          return;
        }
        await _windowChannel.invokeMethod<void>('markReadyToClose');
        return;
      default:
        throw MissingPluginException('No handler for ${call.method}');
    }
  }

  Future<void> _requestExit() async {
    await widget.manager.shutdownOwnedEngine();
    if (!mounted) {
      return;
    }
    await _windowChannel.invokeMethod<void>('markReadyToClose');
  }

  Future<void> _bootstrapWithAutoRetry() async {
    const maxAttempts = 10; // CR-04B: allow backend startup to settle
    Object? lastError;

    for (var attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        if (attempt == 1) {
          await widget.manager.bootstrap();
        } else {
          await widget.manager.reconnect();
        }

        if (widget.manager.snapshot.value.isConnected) {
          return;
        }
      } catch (error) {
        lastError = error;
      }

      if (attempt < maxAttempts) {
        await Future<void>.delayed(const Duration(seconds: 2));
      }
    }

    throw StateError(
      'NEOS could not connect automatically after $maxAttempts attempts.'
      '${lastError == null ? '' : ' Last error: $lastError'}',
    );
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'New Earth Engineering OS',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0F766E)),
        scaffoldBackgroundColor: const Color(0xFFF1F5F9),
      ),
      home: ValueListenableBuilder(
        valueListenable: widget.manager.snapshot,
        builder: (context, engine, _) {
          return FutureBuilder<void>(
            future: _bootstrap,
            builder: (context, bootstrapSnapshot) {
              // CR-04C1B: live manager truth wins over bootstrap-future timing.
              // If NEOS has published a connected engine snapshot, enter the
              // normal shell immediately instead of remaining on Retry while
              // an older bootstrap/reconnect Future is still settling.
              if (engine.isConnected) {
                return NeosShell(
                  client: widget.manager.client,
                  initialServiceUrl:
                      widget.manager.serviceUri?.toString() ??
                      'http://127.0.0.1:8765',
                );
              }

              return _StartupScreen(
                engine: engine,
                onRetry: () {
                  setState(() {
                    _bootstrap = _bootstrapWithAutoRetry();
                  });
                },
                onExit: _requestExit,
              );
            },
          );
        },
      ),
    );
  }
}

class _StartupScreen extends StatelessWidget {
  const _StartupScreen({
    required this.engine,
    required this.onRetry,
    required this.onExit,
  });

  final EngineSnapshot engine;
  final VoidCallback onRetry;
  final Future<void> Function() onExit;

  @override
  Widget build(BuildContext context) {
    final steps = <String>[
      'Starting Engineering Engine',
      'Opening Knowledge Database',
      'Checking Project Registry',
      'Connecting Desktop',
      'Loading Engineering Intelligence',
    ];
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Card(
            elevation: 0,
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'New Earth Engineering OS',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    engine.message,
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                  const SizedBox(height: 20),
                  for (final step in steps)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          Icon(
                            engine.state.index >= steps.indexOf(step)
                                ? Icons.check_circle
                                : Icons.radio_button_unchecked,
                            color: const Color(0xFF0F766E),
                          ),
                          const SizedBox(width: 10),
                          Text(step),
                        ],
                      ),
                    ),
                  const SizedBox(height: 20),
                  if (engine.error != null)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFEE2E2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        engine.error!,
                        style: const TextStyle(color: Color(0xFF991B1B)),
                      ),
                    ),
                  const SizedBox(height: 20),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      if (engine.error != null)
                        FilledButton(
                          onPressed: onRetry,
                          child: const Text('Retry'),
                        ),
                      OutlinedButton(
                        onPressed: () {
                          unawaited(onExit());
                        },
                        child: const Text('Exit'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
