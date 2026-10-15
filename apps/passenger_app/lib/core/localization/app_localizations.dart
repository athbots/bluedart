class AppLocalizations {
  final String languageCode;

  AppLocalizations(this.languageCode);

  static final Map<String, Map<String, String>> _localizedValues = {
    'en': {
      'app_title': 'YatriQ',
      'tagline': 'Know Your Bus Before It Arrives',
      'nearest_stop': 'Nearest Bus Stop',
      'arriving_buses': 'Coming to Your Stop',
      'search_placeholder': 'Search stop or route number...',
      'fastest': 'FASTEST',
      'most_comfortable': 'MOST COMFORTABLE',
      'live_badge': 'LIVE ONBOARD',
      'predicted_badge': 'SMART ESTIMATE',
      'data_delayed': 'UPDATING SOON',
      'route_progression': 'Route Progression',
      'user_stop': 'YOUR STOP',
      'destination': 'DESTINATION',
      'eta_label': 'ETA',
      'minutes_short': 'min',
      'crowd_level': 'Comfort Level',
      'crowd_at_stop': 'At Your Stop',
      'confidence': 'Reliability',
      'updated_ago': 'Updated seconds ago',
      'crowd_low': 'Plenty of Seats',
      'crowd_medium': 'Seats Filling',
      'crowd_high': 'Few Seats Left',
      'crowd_very_high': 'Standing Room Only',
      'switch_lang': 'हिंदी में देखें',
      'best_choice': 'Recommended for You',
      'notify_me': 'Remind 2m Before',
      'offline_cached': 'Schedules saved offline',
    },
    'hi': {
      'app_title': 'यात्रीQ',
      'tagline': 'बस आने से पहले जानें',
      'nearest_stop': 'निकटतम बस स्टॉप',
      'arriving_buses': 'आपके स्टॉप पर आ रही बसें',
      'search_placeholder': 'स्टॉप या बस नंबर खोजें...',
      'fastest': 'सबसे तेज़',
      'most_comfortable': 'सबसे आरामदायक',
      'live_badge': 'लाइव ऑनबोर्ड',
      'predicted_badge': 'स्मार्ट अनुमान',
      'data_delayed': 'जल्द अपडेट हो रहा है',
      'route_progression': 'रूट की स्थिति',
      'user_stop': 'आपका स्टॉप',
      'destination': 'गंतव्य',
      'eta_label': 'आने का समय',
      'minutes_short': 'मिनट',
      'crowd_level': 'सुविधा स्तर',
      'crowd_at_stop': 'आपके स्टॉप पर स्थिति',
      'confidence': 'सटीकता',
      'updated_ago': 'सेकंड पहले अपडेट हुआ',
      'crowd_low': 'पर्याप्त सीटें',
      'crowd_medium': 'सीटें भर रही हैं',
      'crowd_high': 'कम सीटें शेष',
      'crowd_very_high': 'केवल खड़े होने की जगह',
      'switch_lang': 'View in English',
      'best_choice': 'आपके लिए सर्वोत्तम विकल्प',
      'notify_me': '2 मिनट पहले याद दिलाएं',
      'offline_cached': 'समय सारणी ऑफलाइन सुरक्षित है',
    },
  };

  String get(String key) {
    return _localizedValues[languageCode]?[key] ?? _localizedValues['en']?[key] ?? key;
  }
}
