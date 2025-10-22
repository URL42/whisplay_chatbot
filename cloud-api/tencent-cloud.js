const fs = require("fs");
const crypto = require("crypto");
const axios = require("axios");
require("dotenv").config();

// Tencent Cloud ASR
const SECRET_ID = process.env.SECRET_ID;
const SECRET_KEY = process.env.SECRET_KEY;
// const REGION = process.env.REGION;
const ENDPOINT = process.env.ENDPOINT;
const TTS_ENDPOINT = process.env.TTS_ENDPOINT;


const getAuthorization = (payload, service) => {
  const timestamp = Math.floor(Date.now() / 1000);
  const date = new Date(timestamp * 1000).toISOString().slice(0, 10);

  const signStr = (key, msg) =>
    crypto.createHmac("sha256", key).update(msg).digest();

  const getSignatureKey = (key, date, service) => {
    const kDate = signStr("TC3" + key, date);
    const kService = signStr(kDate, service);
    const kSigning = signStr(kService, "tc3_request");
    return kSigning;
  };

  const hashedPayload = crypto
    .createHash("sha256")
    .update(payload)
    .digest("hex");
  const httpRequestMethod = "POST";
  const canonicalUri = "/";
  const canonicalQueryString = "";
  const canonicalHeaders = `content-type:application/json\nhost:${
    service === "asr" ? ENDPOINT : TTS_ENDPOINT
  }\n`;
  const signedHeaders = "content-type;host";
  const canonicalRequest = `${httpRequestMethod}\n${canonicalUri}\n${canonicalQueryString}\n${canonicalHeaders}\n${signedHeaders}\n${hashedPayload}`;
  const algorithm = "TC3-HMAC-SHA256";
  const credentialScope = `${date}/${service}/tc3_request`;
  const stringToSign = `${algorithm}\n${timestamp}\n${credentialScope}\n${crypto
    .createHash("sha256")
    .update(canonicalRequest)
    .digest("hex")}`;
  const signingKey = getSignatureKey(SECRET_KEY, date, service);
  const signature = crypto
    .createHmac("sha256", signingKey)
    .update(stringToSign)
    .digest("hex");
  const authorization = `${algorithm} Credential=${SECRET_ID}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

  return {
    authorization,
    timestamp,
  };
};

const recognizeAudio = async (audioPath) => {
  console.time("识别音频");
  const audioData = fs.readFileSync(audioPath).toString("base64");

  const payload = JSON.stringify({
    EngSerViceType: "16k_zh", // 语音模型
    SourceType: 1,
    Data: audioData,
    DataLen: Buffer.byteLength(audioData),
    VoiceFormat: "mp3", // Changed from 'wav' to 'opus'
  });

  const { authorization, timestamp } = getAuthorization(payload, "asr");

  const headers = {
    Authorization: authorization,
    "Content-Type": "application/json",
    Host: ENDPOINT,
    "X-TC-Action": "SentenceRecognition",
    "X-TC-Timestamp": timestamp,
    "X-TC-Version": "2019-06-14",
    // "X-TC-Region": REGION,
  };

  try {
    const res = await axios.post(`https://${ENDPOINT}`, payload, { headers });
    console.timeEnd("识别音频");
    console.log("识别结果：", res.data.Response.Result);
    return res.data.Response.Result;
  } catch (err) {
    console.error("识别失败：", err.response?.data || err.message);
  }
};

const synthesizeSpeech = async (text) => {
  const payload = JSON.stringify({
    Text: text,
    SessionId: "session-1",
    ModelType: 1,
    Volume: 10,
    Speed: 0,
    ProjectId: 0,
    VoiceType: 601009,
    EmotionCategory: "happy",
    Codec: "mp3",
  });

  const { authorization, timestamp } = getAuthorization(payload, "tts");

  const headers = {
    Authorization: authorization,
    "Content-Type": "application/json",
    Host: TTS_ENDPOINT,
    "X-TC-Action": "TextToVoice",
    "X-TC-Timestamp": timestamp,
    "X-TC-Version": "2019-08-23",
    // "X-TC-Region": REGION,
    EmotionCategory: "happy",
  };

  try {
    const res = await axios.post(`https://${TTS_ENDPOINT}`, payload, {
      headers,
    });
    // console.log('res.data', res.data)
    console.log("合成语音完成");
    return res.data.Response.Audio;
  } catch (err) {
    console.error("合成语音失败：", err.response?.data || err.message);
  }
};

module.exports = {
  recognizeAudio,
  synthesizeSpeech,
};
