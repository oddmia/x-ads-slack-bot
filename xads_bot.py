import requests
from requests_oauthlib import OAuth1
import json
import os
from datetime import datetime, timedelta

# 환경 변수 가져오기
CONSUMER_KEY = os.environ.get('X_CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('X_CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.environ.get('X_ACCESS_TOKEN_SECRET')
ADS_ACCOUNT_ID = os.environ.get('X_ADS_ACCOUNT_ID')
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')

def get_stats():
    url = f"https://ads-api.twitter.com/12/stats/accounts/{ADS_ACCOUNT_ID}"
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    params = {
        'entity': 'ACCOUNT', 'entity_ids': ADS_ACCOUNT_ID,
        'start_time': f"{yesterday}T00:00:00Z", 'end_time': f"{yesterday}T23:59:59Z",
        'granularity': 'DAY', 'metric_groups': 'BILLING,ENGAGEMENT'
    }
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    res = requests.get(url, auth=auth, params=params)
    return res.json()

def send_slack(data):
    # 만약 X API에서 에러를 보냈다면 그 내용을 그대로 슬랙에 출력
    if 'errors' in data:
        error_msg = data['errors'][0].get('message', '알 수 없는 에러')
        code = data['errors'][0].get('code', 'NO_CODE')
        final_msg = f"❌ *X API 에러 발생*\n- 코드: {code}\n- 내용: {error_msg}"
    elif 'data' not in data:
        final_msg = f"❓ *데이터 없음*\n- API 응답 전체: {json.dumps(data)}"
    else:
        # 정상 작동 시 기존 로직
        try:
            metrics = data['data'][0]['id_data'][0]['metrics']
            spend = metrics.get('billed_charge_local_micro', [0])[0] / 1000000
            final_msg = f"📊 *X 광고 실적 ({datetime.now().strftime('%m/%d')})*\n" \
                        f"- 노출수: {metrics.get('impressions', [0])[0]:,}회\n" \
                        f"- 클릭수: {metrics.get('clicks', [0])[0]:,}회\n" \
                        f"- 지출: ${spend:.2f}"
        except Exception as e:
            final_msg = f"⚠️ *코드 가공 에러*: {str(e)}\n- 응답 데이터: {json.dumps(data)}"

    requests.post(SLACK_URL, data=json.dumps({"text": final_msg}))

if __name__ == "__main__":
    result = get_stats()
    send_slack(result)
