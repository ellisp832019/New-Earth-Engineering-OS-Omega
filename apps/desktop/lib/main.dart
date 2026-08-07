import 'package:flutter/widgets.dart';

import 'app.dart';
import 'neos_client.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(NeosApp(client: HttpNeosClient()));
}
