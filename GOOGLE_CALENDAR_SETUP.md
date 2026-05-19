# Google カレンダー連携 セットアップ手順

## 1. パッケージのインストール

```bash
pip install -r requirements.txt
```

または個別に：

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 requests
```

---

## 2. Google Cloud Console の設定

### 2-1. プロジェクト作成・API有効化

1. https://console.cloud.google.com/ にアクセス
2. 新規プロジェクトを作成（または既存プロジェクトを選択）
3. 左メニュー「APIとサービス」→「ライブラリ」
4. 「Google Calendar API」を検索して **有効化**

### 2-2. OAuth 同意画面の設定

1. 「APIとサービス」→「OAuth同意画面」
2. ユーザーの種類：**内部**（社内利用の場合）または **外部**
3. アプリ名・サポートメールを入力して保存
4. スコープに `https://www.googleapis.com/auth/calendar.events` を追加

### 2-3. OAuth 2.0 クライアントIDの作成

1. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
2. アプリケーションの種類：**ウェブ アプリケーション**
3. 承認済みのリダイレクト URI を追加：
   - 開発環境：`http://localhost:8000/reservations/auth/google/callback/`
   - 本番環境：`https://yourdomain.com/reservations/auth/google/callback/`
4. 作成後に表示される **クライアントID** と **クライアントシークレット** を控える

---

## 3. 環境変数の設定

`.env` ファイル（または OS の環境変数）に以下を設定：

```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/reservations/auth/google/callback/
```

`config/settings.py` はすでにこれらの環境変数を読み込む設定になっています。

---

## 4. 動作確認

1. サーバーを起動：`python manage.py runserver`
2. ログイン後、「自分の予約」画面を開く
3. 「Google アカウントで連携する」ボタンをクリック
4. Google の OAuth 認証画面で許可する
5. 「連携中」バッジが表示されれば成功

---

## 5. 同期される内容

| 操作 | Google カレンダーへの反映 |
|------|--------------------------|
| 予約作成 | イベント追加 |
| 予約編集（日時・件名・備考） | イベント更新 |
| ドラッグ＆ドロップで移動 | イベント更新 |
| 予約キャンセル | イベント削除 |

### イベントの内容

- **タイトル**：予約の件名
- **場所**：会議室名
- **説明**：備考 ＋ 参加者名
- **日時**：予約の開始〜終了時刻（終日の場合は終日イベント）

---

## 6. 注意事項

- 連携は **ユーザー単位**です。各ユーザーが自分の Google アカウントで連携する必要があります
- 同期は **このシステム → Google カレンダー** の一方向です（Google カレンダーで変更してもこのシステムには反映されません）
- 「自動同期」をオフにすると新規の同期が停止しますが、既存のイベントは Google カレンダーに残ります
- トークンは `user_google_tokens` テーブルに暗号化なしで保存されます。本番環境では DB の暗号化を検討してください
