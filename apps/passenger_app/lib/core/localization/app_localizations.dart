class AppLocalizations {
  final String languageCode;

  AppLocalizations(this.languageCode);

  static final Map<String, Map<String, String>> _localizedValues = {
    'en': {
      'app_title': 'Smart Transit India',
      'tagline': 'Know Your Bus Before It Arrives',
      'nearest_stop': 'Nearest Bus Stop',
      'arriving_buses': 'Coming to Your Stop',
      'search_placeholder': 'Search stop or route number...',
      'fastest': 'FASTEST',
      'most_comfortable': 'MOST COMFORTABLE',
      'live_badge': 'LIVE CCTV AI',
      'predicted_badge': 'AI PREDICTED',
      'data_delayed': 'DATA DELAYED',
      'route_progression': 'Route Progression',
      'user_stop': 'YOUR STOP',
      'destination': 'DESTINATION',
      'eta_label': 'ETA',
      'minutes_short': 'min',
      'crowd_level': 'Crowd Level',
      'crowd_at_stop': 'Expected at Your Stop',
      'confidence': 'Confidence',
      'updated_ago': 'Updated seconds ago',
      'crowd_low': 'LOW CROWD',
      'crowd_medium': 'MEDIUM CROWD',
      'crowd_high': 'HIGH CROWD',
      'crowd_very_high': 'VERY HIGH CROWD',
      'switch_lang': 'हिंदी में देखें',
    },
    'hi': {
      'app_title': 'स्मार्ट ट्रांजिट इंडिया',
      'tagline': 'बस आने से पहले जानें',
      'nearest_stop': 'निकटतम बस स्टॉप',
      'arriving_buses': 'आपके स्टॉप पर आ रही बसें',
      'search_placeholder': 'स्टॉप या बस नंबर खोजें...',
      'fastest': 'सबसे तेज़',
      'most_comfortable': 'सबसे आरामदायक',
      'live_badge': 'लाइव सीसीटीवी एआई',
      'predicted_badge': 'एआई अनुमानित',
      'data_delayed': 'डेटा विलंबित',
      'route_progression': 'रूट की स्थिति',
      'user_stop': 'आपका स्टॉप',
      'destination': 'गंतव्य',
      'eta_label': 'आने का समय',
      'minutes_short': 'मिनट',
      'crowd_level': 'भीड़ का स्तर',
      'crowd_at_stop': 'आपके स्टॉप पर अनुमानित भीड़',
      'confidence': 'सटीकता',
      'updated_ago': 'सेकंड पहले अपडेट हुआ',
      'crowd_low': 'कम भीड़',
      'crowd_medium': 'मध्यम भीड़',
      'crowd_high': 'अधिक भीड़',
      'crowd_very_high': 'अत्यधिक भीड़',
      'switch_lang': 'View in English',
    },
  };

  String get(String key) {
    return _localizedValues[languageCode]?[key] ?? _localizedValues['en']?[key] ?? key;
  }
}
