
import axios from 'axios';

class QQApi {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
  }
  
  async getAllIntelligence() {
    const responses = await Promise.all([
      this.getConsciousness(),
      this.getASIExcellence(),
      this.getGAUGEAssets()
    ]);
    
    return {
      consciousness: responses[0],
      asi: responses[1],
      gauge: responses[2]
    };
  }
  
  async getConsciousness() {
    const response = await axios.get(`${this.baseURL}/api/quantum-consciousness`);
    return response.data;
  }
  
  async getASIExcellence() {
    const response = await axios.get(`${this.baseURL}/api/asi-excellence`);
    return response.data;
  }
  
  async getGAUGEAssets() {
    const response = await axios.get(`${this.baseURL}/api/gauge-assets`);
    return response.data;
  }
}

export const qqApi = new QQApi();
