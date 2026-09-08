import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'ai_service.dart';

class AIScreen extends StatefulWidget {
  const AIScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<AIScreen> createState() => _AIScreenState();
}

class _AIScreenState extends State<AIScreen> {
  late final AIService _ai = AIService(widget.api);
  final _question = TextEditingController();

  final List<Map<String, String>> _messages = [
    {
      'role': 'assistant',
      'text': 'Ask FinPilot about your spending, savings, budgets, or goals.',
    }
  ];

  bool _loading = false;

  Future<void> _send() async {
    final question = _question.text.trim();
    if (question.isEmpty || _loading) return;

    setState(() {
      _messages.add({'role': 'user', 'text': question});
      _question.clear();
      _loading = true;
    });

    try {
      final answer = await _ai.ask(question);
      if (!mounted) return;
      setState(() => _messages.add({'role': 'assistant', 'text': answer}));
    } on DioException catch (error) {
      final detail = error.response?.data;
      final message = detail is Map<String, dynamic> && detail['detail'] != null
          ? detail['detail'].toString()
          : 'FinPilot AI is unavailable right now.';
      if (!mounted) return;
      setState(() => _messages.add({'role': 'assistant', 'text': message}));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _question.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('FinPilot AI')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message['role'] == 'user';
                return Align(
                  alignment: isUser
                      ? Alignment.centerRight
                      : Alignment.centerLeft,
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 320),
                        child: Text(message['text'] ?? ''),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _question,
                      minLines: 1,
                      maxLines: 4,
                      onSubmitted: (_) => _send(),
                      decoration: const InputDecoration(
                        hintText: 'Ask about your money...',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _loading ? null : _send,
                    icon: _loading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
