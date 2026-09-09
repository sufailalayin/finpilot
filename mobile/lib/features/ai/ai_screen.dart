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
  final _scroll = ScrollController();

  final List<Map<String, String>> _messages = [
    {
      'role': 'assistant',
      'text': 'Ask FinPilot about your spending, savings, budgets, or goals.',
    }
  ];

  bool _loading = false;

  void _scrollToLatest() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) return;
      _scroll.animateTo(
        _scroll.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  final _prompts = const [
    'Can I afford a ₹25,000 purchase this month?',
    'What is hurting my financial health score?',
    'How should I reduce my EMI burden?',
    'Which budget is most likely to overspend?',
    'How much should I save monthly for my goals?',
    'What should I focus on for the next 30 days?',
  ];

  Future<void> _brief() async {
    if (_loading) return;
    setState(() => _loading = true);
    try {
      final answer = await _ai.brief();
      if (!mounted) return;
      setState(() {
        _messages.add({
          'role': 'assistant',
          'text': 'Copilot Brief\n\n' + answer,
        });
      });
      _scrollToLatest();
    } on DioException catch (error) {
      final detail = error.response?.data;
      final message = detail is Map<String, dynamic> && detail['detail'] != null
          ? detail['detail'].toString()
          : 'FinPilot AI is unavailable right now.';
      if (!mounted) return;
      setState(() => _messages.add({'role': 'assistant', 'text': message}));
      _scrollToLatest();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _send() async {
    final question = _question.text.trim();
    if (question.isEmpty || _loading) return;

    setState(() {
      _messages.add({'role': 'user', 'text': question});
      _question.clear();
      _loading = true;
    });
    _scrollToLatest();

    try {
      final answer = await _ai.ask(question);
      if (!mounted) return;
      setState(() => _messages.add({'role': 'assistant', 'text': answer}));
      _scrollToLatest();
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
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('FinPilot AI')),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              controller: _scroll,
              padding: const EdgeInsets.all(16),
              children: [
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(22),
                  ),
                  child: const Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.auto_awesome, size: 28),
                      SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'FinPilot AI',
                              style: TextStyle(
                                fontWeight: FontWeight.w800,
                                fontSize: 18,
                              ),
                            ),
                            SizedBox(height: 5),
                            Text(
                              'Ask across your balances, spending, budgets, goals, assets, loans, EMIs, bills and financial health.',
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.tonalIcon(
                    onPressed: _loading ? null : _brief,
                    icon: const Icon(Icons.summarize_outlined),
                    label: const Text('Generate Copilot Brief'),
                  ),
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _prompts
                      .map(
                        (prompt) => ActionChip(
                          label: Text(prompt),
                          onPressed: _loading
                              ? null
                              : () {
                                  _question.text = prompt;
                                  _send();
                                },
                        ),
                      )
                      .toList(),
                ),
                const SizedBox(height: 18),
                ..._messages.map((message) {
                  final isUser = message['role'] == 'user';
                  return Align(
                    alignment: isUser
                        ? Alignment.centerRight
                        : Alignment.centerLeft,
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      constraints: const BoxConstraints(maxWidth: 330),
                      decoration: BoxDecoration(
                        color: isUser
                            ? Theme.of(context).colorScheme.primaryContainer
                            : Theme.of(context).colorScheme.surfaceContainerHigh,
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: Text(message['text'] ?? ''),
                    ),
                  );
                }),
              ],
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
