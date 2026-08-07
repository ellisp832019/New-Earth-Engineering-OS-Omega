import 'package:flutter/widgets.dart';

import 'bootstrap.dart';
import 'engine_manager.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(NeosBootstrapApp(manager: NeosEngineManager()));
}
