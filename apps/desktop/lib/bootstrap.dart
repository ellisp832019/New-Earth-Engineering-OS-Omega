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
  late Future<void> _bootstrap = widget.manager.bootstrap().then((_) {});

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
      home: FutureBuilder<void>(
        future: _bootstrap,
        builder: (context, snapshot) {
          final engine = widget.manager.snapshot.value;
          if (snapshot.connectionState != ConnectionState.done || !engine.isConnected) {
            return _StartupScreen(
              engine: engine,
              onRetry: () {
                setState(() {
                  _bootstrap = widget.manager.reconnect().then((_) {});
                });
              },
              onExit: _requestExit,
            );
          }
          return NeosShell(
            client: widget.manager.client,
            initialServiceUrl: widget.manager.serviceUri?.toString() ?? 'http://127.0.0.1:8765',
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
                  Text('New Earth Engineering OS', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  Text(engine.message, style: Theme.of(context).textTheme.bodyLarge),
                  const SizedBox(height: 20),
                  for (final step in steps)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          Icon(
                            engine.state.index >= steps.indexOf(step) ? Icons.check_circle : Icons.radio_button_unchecked,
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
                      child: Text(engine.error!, style: const TextStyle(color: Color(0xFF991B1B))),
                    ),
                  const SizedBox(height: 20),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      FilledButton(onPressed: onRetry, child: const Text('Retry')),
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
