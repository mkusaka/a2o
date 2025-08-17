# Claude Code Setup with LiteLLM Proxy

## Claude CodeでLiteLLM Proxyを使用する設定

Claude CodeをAWS LambdaにデプロイしたLiteLLM Proxy経由で使用するための設定方法です。

### 1. 環境変数を設定してClaude Codeを起動

```bash
# Basic認証情報を含めたProxyのURLを設定
export ANTHROPIC_BASE_URL="https://demo:k9VgX46OirLQnqgXOye2jXlap5vDF4ob@vhg6zetavh.execute-api.us-east-1.amazonaws.com"

# Claude Codeを起動
claude
```

### 2. グローバル設定として保存（推奨）

```bash
# Claude Codeの設定に追加
claude config set --global env '{
  "ANTHROPIC_BASE_URL": "https://demo:k9VgX46OirLQnqgXOye2jXlap5vDF4ob@vhg6zetavh.execute-api.us-east-1.amazonaws.com"
}'
```

### 3. または設定ファイルを直接編集

`~/.claude/settings.json` を編集:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://demo:k9VgX46OirLQnqgXOye2jXlap5vDF4ob@vhg6zetavh.execute-api.us-east-1.amazonaws.com"
  }
}
```

### 注意事項

- URLにBasic認証情報を含める形式: `https://username:password@domain.com`
- LiteLLM ProxyはOpenAI互換APIを提供しますが、Claude CodeはAnthropic APIを期待するため、モデル名のマッピングが必要な場合があります
- 現在の設定では以下のモデルが利用可能:
  - `gpt-4o-mini` (OpenAI)
  - `claude-3-5-sonnet` (Anthropic)

### テスト方法

設定後、Claude Codeで以下のコマンドを実行してテスト:

```bash
claude "Hello, can you confirm you're working?"
```

### トラブルシューティング

認証エラーが発生する場合:
1. Basic認証の資格情報を確認
2. URLエンコードが必要な特殊文字がパスワードに含まれていないか確認
3. AWS Lambda関数が正常に動作しているか確認: 
   ```bash
   curl https://vhg6zetavh.execute-api.us-east-1.amazonaws.com/health
   ```