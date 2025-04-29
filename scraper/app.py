from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    
    if not data or 'company_name' not in data:
        return jsonify({'error': 'Missing company name'}), 400
        
    company_name = data['company_name']
    
    # Simple response for now
    return jsonify({
        'company_name': company_name,
        'message': f'Your Company Name is {company_name}'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)