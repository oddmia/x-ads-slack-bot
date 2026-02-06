import requests
from requests_oauthlib import OAuth1
import json
import os
from datetime import datetime, timedelta

# 깃허브 보안 설정값 가져오기
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
    try:
        metrics = data['data'][0]['id_data'][0]['metrics']
        # 지출 비용 계산 (마이크로 단위이므로 1,000,000으로 나눔)
        spend = metrics.get('billed_charge_local_micro', [0])[0] / 1000000
        msg = f"📊 *X 광고 실적 ({datetime.now().strftime('%m/%d')})*\n" \
              f"- 노출수: {metrics.get('impressions', [0])[0]:,}회\n" \
              f"- 클릭수: {metrics.get('clicks', [0])[0]:,}회\n" \
              f"- 지출: ${spend:.2f}"
        requests.post(SLACK_URL, data=json.dumps({"text": msg}))
    except Exception as e:
        requests.post(SLACK_URL, data=json.dumps({"text": f"❌ 에러 발생: {str(e)}"}))

if __name__ == "__main__":
    result = get_stats()
    send_slack(result)