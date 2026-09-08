import '../../core/api_client.dart';

class AIService {
  AIService(this._api);

  final ApiClient _api;

  Future<String> ask(String question) async {
    final response = await _api.dio.post(
      '/ai/ask',
      data: {'question': question.trim()},
    );
    return response.data['answer'].toString();
  }
}
