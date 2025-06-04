/**
 * TRAXOVO Mobile App Entry Point
 * React Native application for iOS and Android
 */

import { AppRegistry } from 'react-native';
import App from './App';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);