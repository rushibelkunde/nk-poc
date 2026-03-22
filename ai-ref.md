import dotenv from "dotenv";
dotenv.config();
import fs from "fs";
import path from "path";
import os from "os";

import { DEFAULT_LLM_MODEL, DEFAULT_PROVIDER } from "./llm-models";
import {
  getAiAssessmentPrompt,
  getAnalysisPrompt,
  getResumeInsightsPrompt,
  getScreeningQuestionsPrompt,
  getSingleQuestionPrompt,
} from "./promptTemplates";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { cleanJsonOutput } from "~/utils/json-helper";
import { downloadFile } from "./langchain.server";
import { MediaFactory } from "~/lib/media/media-factory.server";

const config = {
  aiProviderOrchestrationAPIURL:
    process.env.AI_PROVIDER_ORCHESTRATION_API_URL || "",
  aiProviderOrchestrationAPIKey:
    process.env.AI_PROVIDER_ORCHESTRATION_API_KEY || "",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${
      process.env.AI_PROVIDER_ORCHESTRATION_API_KEY || ""
    }`,
  },
};

/**
 * Reusable function to call AI Provider Orchestration API
 * @param modelName - The model to use for generation
 * @param provider - The provider to use
 * @param systemPrompt - System prompt object with role and content
 * @param userPrompt - User prompt object with role and content
 * @returns Object containing parsed result and token usage
 */
async function callAiProviderOrchestration(
  modelName: string,
  provider: string,
  systemPrompt: { role: string; content: string | any },
  userPrompt: { role: string; content: string | any },
) {
  const response = await fetch(
    config.aiProviderOrchestrationAPIURL + "/ai/generate",
    {
      method: "POST",
      headers: config.headers,
      body: JSON.stringify({
        model: modelName,
        provider: provider,
        prompts: [systemPrompt, userPrompt],
      }),
    },
  );

  if (!response.ok) {
    const errorBody = await response.text();
    console.error("AI API Error Body:", errorBody);
    throw new Error(
      `AI Provider Orchestration API error: ${response.status} ${response.statusText} - ${errorBody}`,
    );
  }

  const res = await response.json();

  return res;
}

export const transcribeAudio = async (audioPath: string) => {
  const provider = DEFAULT_PROVIDER; // This can be dynamic based on modelName or other criteria

  let tempFilePath: string | null = null;
  let compressedFilePath: string | null = null;

  try {
    console.log("Transcribing audio from URL:", audioPath);

    let filePathToSend: string;

    // 1. Resolve Input File
    if (audioPath.startsWith("http") || audioPath.startsWith("https")) {
      const response = await fetch(
        config.aiProviderOrchestrationAPIURL + "/audio/transcribe",
        {
          method: "POST",
          headers: config.headers,
          body: JSON.stringify({ audio_url: audioPath, provider }),
        },
      );

      if (!response.ok) {
        throw new Error(
          `Transcription API error: ${response.status} ${response.statusText}`,
        );
      }

      const res = await response.json();
      return res.transcription;
    }

    // Local file path
    const rootDir = process.cwd();
    // Remove leading slash or 'uploads/' prefix handling if needed, but usually it's relative
    const relativePath = audioPath.startsWith("/")
      ? audioPath.slice(1)
      : audioPath;
    filePathToSend = path.join(rootDir, relativePath);

    if (!fs.existsSync(filePathToSend)) {
      throw new Error(`Local file not found: ${filePathToSend}`);
    }

    // 2. Check Size and Compress if needed
    const stats = fs.statSync(filePathToSend);
    if (stats.size > 10 * 1024 * 1024) {
      console.log(`File size ${stats.size} exceeds 10MB limit. Compressing...`);
      compressedFilePath = path.join(
        os.tmpdir(),
        `temp_audio_comp_${Date.now()}.mp3`,
      );

      try {
        const mediaProcessor = MediaFactory.getProcessor(
          process.env.MEDIA_PROCESSOR_TYPE as any
        );
        await mediaProcessor.compressAudio(filePathToSend, compressedFilePath);
        filePathToSend = compressedFilePath;
        const newStats = fs.statSync(compressedFilePath);
        console.log(`Compressed file size: ${newStats.size}`);
      } catch (compErr) {
        console.error("Compression failed:", compErr);
        // Fallback to original, might fail at OpenAI
      }
    }

    // 3. Transcribe
    // Option 1: Using fs.readFileSync (simpler)
    const fileBuffer = fs.readFileSync(filePathToSend);
    const blob = new Blob([fileBuffer]);

    const formData = new FormData();
    formData.append("file", blob, path.basename(filePathToSend)); // Include filename
    formData.append("provider", provider);

    console.log(`Uploading file: ${filePathToSend}, size: ${stats.size} bytes`);

    const response = await fetch(
      config.aiProviderOrchestrationAPIURL + "/audio/transcribe",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${config.aiProviderOrchestrationAPIKey}`,
          // DO NOT set content-type - let FormData set it automatically
        },
        body: formData,
        signal: AbortSignal.timeout(300000), // 5 minutes
      },
    );

    if (!response.ok) {
      throw new Error(
        `Transcription API error: ${response.status} ${response.statusText}`,
      );
    }
    const res = await response.json();

    return res.transcription; // OpenAI returns string if response_format is text
  } catch (error) {
    console.error("Transcription error:", error);
    return null;
  } finally {
    // 4. Cleanup
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      try {
        fs.unlinkSync(tempFilePath);
      } catch (e) {
        console.error("Failed to cleanup temp download:", e);
      }
    }
    if (compressedFilePath && fs.existsSync(compressedFilePath)) {
      try {
        fs.unlinkSync(compressedFilePath);
      } catch (e) {
        console.error("Failed to cleanup compressed file:", e);
      }
    }
  }
};

export const generateInsightsFromResume = async (
  resumeText: string,
  modelName: string = DEFAULT_LLM_MODEL,
) => {
  const provider = DEFAULT_PROVIDER; // This can be dynamic based on modelName or other criteria
  const prompt = getResumeInsightsPrompt(resumeText);

  const message = new HumanMessage(prompt);
  const userPrompt = { role: "user", content: message.content };

  // Add a system message to enforce JSON
  const sysMsg = new SystemMessage(
    "You are a JSON-only API. Never output explanatory text.",
  );
  const systemPrompt = { role: "system", content: sysMsg.content };

  const res = await callAiProviderOrchestration(
    modelName,
    provider,
    systemPrompt,
    userPrompt,
  );

  let totalTokens = 0;
  if (res && res.total_tokens) {
    totalTokens = res.total_tokens || 0;
  }

  let content = res.response as string;

  // Clean JSON output by removing markdown code blocks
  if (content.startsWith("```json")) {
    content = content
      .replace(/^```json/, "")
      .replace(/```$/, "")
      .trim();
  } else if (content.startsWith("```")) {
    content = content.replace(/^```/, "").replace(/```$/, "").trim();
  }

  try {
    const result = JSON.parse(content);
    return { result, usage: { total_tokens: totalTokens } };
  } catch (err) {
    console.log(err);
    console.error("Error parsing LLM response:", content);
    return { result: null, usage: { total_tokens: totalTokens } };
  }
};

export async function generateScreeningQuestions(
  resumeText: string,
  role: string,
  responsibilities: string,
  skills: string[],
  numberOfQuestions: number,
  modelName: string = DEFAULT_LLM_MODEL,
) {
  const provider = DEFAULT_PROVIDER; // This can be dynamic based on modelName or other criteria

  const message = new HumanMessage(
    getScreeningQuestionsPrompt(
      resumeText,
      role,
      responsibilities,
      skills,
      numberOfQuestions,
    ),
  );

  const userPrompt = { role: "user", content: message.content };

  // Add a system message to enforce JSON
  const sysMsg = new SystemMessage(
    "You are a JSON-only API. Never output explanatory text.",
  );
  const systemPrompt = { role: "system", content: sysMsg.content };

  const res = await callAiProviderOrchestration(
    modelName,
    provider,
    systemPrompt,
    userPrompt,
  );

  let totalTokens = 0;
  if (res && res.total_tokens) {
    totalTokens = res.total_tokens || 0;
  }

  let content = res.response as string;

  // Clean JSON output by removing markdown code blocks
  if (content.startsWith("```json")) {
    content = content
      .replace(/^```json/, "")
      .replace(/```$/, "")
      .trim();
  } else if (content.startsWith("```")) {
    content = content.replace(/^```/, "").replace(/```$/, "").trim();
  }

  try {
    const result = JSON.parse(content);
    return { result, usage: { total_tokens: totalTokens } };
  } catch (err) {
    console.log(err);
    console.error("Error parsing LLM response:", content);
    return { result: null, usage: { total_tokens: totalTokens } };
  }
}

export const generateAiAssessment = async (
  mode: string, // 'quiz' | 'coding' | 'frontend'
  candidateLevel: string,
  categories: Array<{
    name: string;
    description: string;
    count: number;
    difficultyDistribution: { easy: number; medium: number; hard: number };
    allowedQuestionTypes?: string[];
  }>,
  language: string,
  modelName: string = DEFAULT_LLM_MODEL,
) => {
  const provider = DEFAULT_PROVIDER; // This can be dynamic based on modelName or other criteria

  let totalTokens = 0;
  let allQuestions: any[] = [];

  // Iterate through each category configuration to ensure specific requirements are met
  for (const cat of categories) {
    // We break down by difficulty to ensure exact distribution
    const total = cat.count;
    const easyCount = Math.floor(
      (cat.difficultyDistribution.easy / 100) * total,
    );
    const hardCount = Math.floor(
      (cat.difficultyDistribution.hard / 100) * total,
    );
    const mediumCount = total - easyCount - hardCount;

    const batches = [
      { diff: "Easy", count: easyCount },
      { diff: "Medium", count: mediumCount },
      { diff: "Hard", count: hardCount },
    ].filter((b) => b.count > 0);

    for (const batch of batches) {
      try {
        const promptText = getAiAssessmentPrompt(
          mode,
          cat.name,
          cat.description,
          batch.count,
          batch.diff,
          candidateLevel,
          cat.allowedQuestionTypes || [],
          language,
        );

        const message = new HumanMessage(promptText);
        const userPrompt = { role: "user", content: message.content };

        // Add a system message to enforce JSON
        const sysMsg = new SystemMessage(
          "You are a JSON-only API. Never output explanatory text.",
        );
        const systemPrompt = { role: "system", content: sysMsg.content };

        const res = await callAiProviderOrchestration(
          modelName,
          provider,
          systemPrompt,
          userPrompt,
        );

        // Accumulate tokens
        if (res && res.total_tokens) {
          totalTokens += res.total_tokens || 0;
        }

        const cleanJson = cleanJsonOutput(res.response as string);
        const parsedQuestions = JSON.parse(cleanJson);

        // Post-processing to ensure internal fields exist
        const processed = parsedQuestions.map((q: any) => ({
          ...q,
          _id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`, // Frontend temp ID
          isAiGenerated: true,
          category: cat.name, // Force the category name
          aiMetadata: {
            candidateLevel,
            difficultyRequest: batch.diff,
            originalPromptTopic: cat.name,
          },
        }));

        allQuestions = [...allQuestions, ...processed];
      } catch (err: any) {
        console.error(
          `Error generating questions for ${cat.name} (${batch.diff}):`,
          err,
        );
        // Continue to next batch even if one fails
      }
    }
  }

  return { result: allQuestions, usage: { total_tokens: totalTokens } };
};

export async function generateSingleAiQuestion(
  mode: string,
  candidateLevel: string,
  oldQuestion: any,
  language: string,
  modelName: string = DEFAULT_LLM_MODEL,
) {
  const provider = DEFAULT_PROVIDER; // This can be dynamic based on modelName or other criteria

  try {
    const promptText = getSingleQuestionPrompt(
      mode,
      oldQuestion.category, // Use category from the question itself
      oldQuestion.text || oldQuestion.title, // Pass old text as context
      oldQuestion.aiMetadata?.difficultyRequest || "Medium", // Try to preserve difficulty
      candidateLevel,
      oldQuestion.questionType,
      language,
    );

    const message = new HumanMessage(promptText);
    const userPrompt = { role: "user", content: message.content };

    // Add a system message to enforce JSON
    const sysMsg = new SystemMessage(
      "You are a JSON-only API. Never output explanatory text.",
    );
    const systemPrompt = { role: "system", content: sysMsg.content };

    const res = await callAiProviderOrchestration(
      modelName,
      provider,
      systemPrompt,
      userPrompt,
    );

    let totalTokens = 0;
    if (res && res.total_tokens) {
      totalTokens = res.total_tokens || 0;
    }

    // Assuming you have a cleanJsonOutput helper
    const cleanJson = cleanJsonOutput(res.response as string);

    // Parse result (AI might return object or array of 1 object)
    let parsed = JSON.parse(cleanJson);
    if (Array.isArray(parsed)) parsed = parsed[0];

    // Merge strictly with necessary metadata
    const result = {
      ...parsed,
      _id: oldQuestion._id, // KEEP THE SAME ID so frontend doesn't lose track? Or generate new?
      isAiGenerated: true,
      category: oldQuestion.category, // Ensure category persists
      aiMetadata: oldQuestion.aiMetadata, // Ensure difficulty metadata persists
    };

    return { result, usage: { total_tokens: totalTokens } };
  } catch (err: any) {
    console.error("Single Gen Error:", err);
    return null;
  }
}

export async function generateAnswerAnalysis(
  questionText: string,
  answerText: string,
  questionType: string,
  videoPath?: string, // Optional video path or URL
  modelName: string = DEFAULT_LLM_MODEL,
) {
  const provider = DEFAULT_PROVIDER; // This can be dynamic based on modelName or other criteria

  let tempVideoPath: string | null = null;
  let localVideoPath = videoPath?.startsWith("/")
    ? videoPath.slice(1)
    : videoPath;

  try {
    if (!answerText || answerText.trim() === "") {
      return {
        feedback: "No answer provided.",
        rating: 0,
        key_points: [],
      };
    }

    // Handle Remote URL
    if (
      videoPath &&
      (videoPath.startsWith("http") || videoPath.startsWith("https"))
    ) {
      try {
        const url = new URL(videoPath);
        const ext = path.extname(url.pathname) || ".webm"; // default to webm if unknown
        tempVideoPath = path.join(
          os.tmpdir(),
          `temp_vid_${Date.now()}_${Math.random()
            .toString(36)
            .substring(7)}${ext}`,
        );
        console.log(
          `[AI-Analysis] Downloading remote video from ${videoPath} to ${tempVideoPath}`,
        );
        await downloadFile(videoPath, tempVideoPath);
        localVideoPath = tempVideoPath;
      } catch (dlErr) {
        console.error("[AI-Analysis] Failed to download remote video:", dlErr);
        // Fallback: Try with original path, though it will likely fail GStreamer if it's a URL
      }
    }

    let totalTokens = 0;

    // 1. Basic Text Analysis
    const promptText = getAnalysisPrompt(
      questionText,
      answerText,
      questionType,
    );
    const message = new HumanMessage(promptText);
    const userPrompt = { role: "user", content: message.content };

    // Add a system message to enforce JSON
    const sysMsg = new SystemMessage("You are a JSON-only API.");
    const systemPrompt = { role: "system", content: sysMsg.content };

    const res = await callAiProviderOrchestration(
      modelName,
      provider,
      systemPrompt,
      userPrompt,
    );

    if (res && res.total_tokens) {
      totalTokens += res.total_tokens || 0;
    }

    const cleanJson = cleanJsonOutput(res.response as string);
    let analysisResult = JSON.parse(cleanJson);

    // 2. Multimedia Analysis (if video exists)
    if (localVideoPath && fs.existsSync(localVideoPath)) {
      const frameDir = path.join(
        path.dirname(localVideoPath),
        "frames_" + Date.now(),
      );

      try {
        // Use functions from gstreamer.server.ts
        const mediaProcessor = MediaFactory.getProcessor(
          process.env.MEDIA_PROCESSOR_TYPE as any
        );
        console.log(
          `[AI-Analysis] Extracting frames from ${localVideoPath} to ${frameDir}`
        );
        const frames = await mediaProcessor.extractFrames(
          localVideoPath,
          frameDir
        );
        console.log(`[AI-Analysis] Extracted ${frames.length} frames`);
        const silenceDuration = await mediaProcessor.detectSilence(
          localVideoPath
        );

        analysisResult.silenceDuration = parseFloat(silenceDuration.toFixed(2));

        if (frames.length > 0) {
          // Chunk frames into batches to analyze the entire video
          const BATCH_SIZE = 10; // Adjust as needed
          const chunks = [];
          for (let i = 0; i < frames.length; i += BATCH_SIZE) {
            chunks.push(frames.slice(i, i + BATCH_SIZE));
          }

          const chunkResults: any[] = [];
          console.log(
            `[AI-Analysis] Processing ${chunks.length} chunks of frames...`,
          );

          for (let i = 0; i < chunks.length; i++) {
            const chunkFrames = chunks[i];
            const visionContent = [
              {
                type: "text",
                text: `Analyze these frames (Part ${i + 1}/${
                  chunks.length
                }) from an interview video. response should be strictly json, Provide a JSON object with : 1. 'facialAnalysis': { 'emotion': string, 'confidence': number (0-1) }, 2. 'bodyLanguage': string (short description), 3. 'eyeTracking': { 'focused': boolean, 'offScreenPercentage': number (0-100 estimate) }, 4. 'backgroundNoise': string (visual clues or general environment), 5. 'multipleFacesDetected': boolean.`,
              },
            ];

            for (const framePath of chunkFrames) {
              const image = fs.readFileSync(framePath);
              const base64Image = image.toString("base64");
              visionContent.push({
                type: "image_url",
                image_url: {
                  url: `data:image/jpeg;base64,${base64Image}`,
                },
              } as any);
            }

            const visionMessage = new HumanMessage({
              content: visionContent,
            });

            const userPrompt = { role: "user", content: visionMessage.content };
            const systemPrompt = {
              role: "system",
              content: "You are a JSON-only API.",
            };
            try {
              const visionRes = await callAiProviderOrchestration(
                modelName,
                provider,
                systemPrompt,
                userPrompt,
              );

              if (visionRes && visionRes.total_tokens) {
                totalTokens += visionRes.total_tokens || 0;
              }

              const visionJson = cleanJsonOutput(visionRes.response as string);
              if (visionJson) {
                chunkResults.push(JSON.parse(visionJson));
              }
            } catch (e) {
              console.error(
                `[AI-Analysis] Failed to analyze chunk ${i + 1}:`,
                e,
              );
            }
          }

          // Aggregate results
          if (chunkResults.length > 0) {
            const aggregated = {
              facialAnalysis: { emotion: "Neutral", confidence: 0 },
              bodyLanguage: "",
              eyeTracking: { focused: true, offScreenPercentage: 0 },
              backgroundNoise: "",
              multipleFacesDetected: false,
            };

            // Helpers for aggregation
            const emotions: Record<string, number> = {};
            let totalConfidence = 0;
            let totalOffScreen = 0;
            let focusedCount = 0;
            const bodyLangParts: string[] = [];
            const noiseParts: string[] = [];

            chunkResults.forEach((res) => {
              // Emotion
              if (res.facialAnalysis) {
                const e = res.facialAnalysis.emotion || "Unknown";
                emotions[e] = (emotions[e] || 0) + 1;
                totalConfidence += res.facialAnalysis.confidence || 0;
              }
              // Eye Tracking
              if (res.eyeTracking) {
                totalOffScreen += res.eyeTracking.offScreenPercentage || 0;
                if (res.eyeTracking.focused) focusedCount++;
              }
              // Boolean flags
              if (res.multipleFacesDetected)
                aggregated.multipleFacesDetected = true;
              // Text descriptions
              if (res.bodyLanguage) bodyLangParts.push(res.bodyLanguage);
              if (res.backgroundNoise) noiseParts.push(res.backgroundNoise);
            });

            // Finalizing Emotion (Dominant)
            let dominantEmotion = "Neutral";
            let maxCount = 0;
            Object.entries(emotions).forEach(([e, count]) => {
              if (count > maxCount) {
                maxCount = count;
                dominantEmotion = e;
              }
            });
            aggregated.facialAnalysis.emotion = dominantEmotion;
            aggregated.facialAnalysis.confidence =
              totalConfidence / chunkResults.length;

            // Finalizing Eye Tracking (Average)
            aggregated.eyeTracking.offScreenPercentage = Math.round(
              totalOffScreen / chunkResults.length,
            );
            aggregated.eyeTracking.focused =
              focusedCount > chunkResults.length / 2;

            // Finalizing Text (Concatenate unique or summarize)
            // Simple concatenation for now, maybe taking the first non-empty or unique ones
            aggregated.bodyLanguage = [...new Set(bodyLangParts)].join(". ");
            aggregated.backgroundNoise = [...new Set(noiseParts)].join(". ");

            analysisResult = { ...analysisResult, ...aggregated };
          }

          // Cleanup frames
          frames.forEach((f) => {
            try {
              fs.unlinkSync(f);
            } catch {}
          });
          try {
            fs.rmdirSync(frameDir);
          } catch {}
        }
      } catch (vidErr) {
        console.error("Video analysis failed:", vidErr);
      }
    }

    return { result: analysisResult, usage: { total_tokens: totalTokens } };
  } catch (err: any) {
    console.error("Analysis Error:", err);
    return null;
  } finally {
    // Cleanup temp video file if downloaded
    if (tempVideoPath && fs.existsSync(tempVideoPath)) {
      try {
        fs.unlinkSync(tempVideoPath);
        console.log(`[AI-Analysis] Cleaned up temp video: ${tempVideoPath}`);
      } catch (cleanupErr) {
        console.error(
          `[AI-Analysis] Failed to cleanup temp video ${tempVideoPath}:`,
          cleanupErr,
        );
      }
    }
  }
}