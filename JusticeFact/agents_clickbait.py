import json
import os.path
from utils import generate_res,generate_score
from Web_search import Web_search
from tqdm import tqdm
import pandas as pd
import pickle
import csv
import re
import os
import time 
from io import StringIO

from Jury_Selection import  get_profession_prompts , get_profession2_prompts




def run_reason():

    
    #作为组织者，根据标题内容和立场整理出需要搜索内容
    keyword_prompt = "Goal: As an organizer, your task is to extract a set of keywords or search phrases based on the content of the headline and the {} stance (assuming the headline is {}). These keywords will be used to perform real-time web searches that help verify whether the headline is clickbait.\n\n"
    keyword_prompt += "Requirement 1: The headline content is {}.\n"
    keyword_prompt += "Requirement 2: Read the headline carefully and identify key phrases, exaggerated claims, misleading cues, or referenced entities (people, places, organizations).\n"
    keyword_prompt += "Requirement 3: Strictly stand on the standpoint of {} to generate **accurate and verifiable** keywords or search phrases to help {}'s reasoning that the headline is {}.\n"
    keyword_prompt += "Requirement 4: Do not include speculative or emotional content. Focus on:\n"
    "   - Named entities or referenced sources\n"
    "   - Implied events or outcomes\n"
    "   - Sensational or exaggerated claims\n"
    "   - Alleged controversies or surprises\n"
    keyword_prompt += "Requirement 5: The content that must be searched by using the keywords should be related to the actual events or facts behind the headline.\n"
    keyword_prompt += "Requirement 6: Do **not** include any explanatory text.\n"
    keyword_prompt += "Requirement 7: Put the output content into []. Do not add any other text outside the brackets.\n"


    #作为控方律师，请从该视角出发，陈述标题为什么可能是点击诱饵。
    prosecutor_prompt = "Goal: As a prosecutor, based on your knowledge base, filter online search results, and combined with the reasoning perspective and headline content, it is forcibly inferred that the headline is clickbait.\n"
    prosecutor_prompt += "Requirement 1: The headline content is {}.\n"
    prosecutor_prompt += "Requirement 2: Online search content to be filtered: {}.\n"
    prosecutor_prompt += "Requirement 3: Reasoning should be based on the following perspectives of the headline, that is, the reasoning perspective is {}.\n"
    prosecutor_prompt += "Requirement 4: Filtering requirements: The filtered results must be highly relevant to the reasoning perspective and headline content, and meet the purpose of determining that the headline is clickbait.\n"
    prosecutor_prompt += "Requirement 5: Reasoning should be based on your own knowledge base, headline content, reasoning perspective, and filtered online search content.\n"
    prosecutor_prompt += "Requirement 6: The generated reasoning content must strongly prove that the headline is clickbait, and cannot contain uncertain expressions or words such as 'possibility', 'maybe', or 'authenticity'.\n"
    prosecutor_prompt += "Requirement 7: The reasoning must be carried out in the order of reasoning angles, and the reasoning content generated from different reasoning angles is separated by ';'.\n"
    prosecutor_prompt += "Requirement 8: The number of reasoning words should not exceed 120 words.\n"
    prosecutor_prompt += "Requirement 9: Put the output content into [].\n"


    #作为辩方律师，请从该视角出发，陈述新闻为什么可能是真的。
    defense_prompt = "Goal: As a defense lawyer, based on your knowledge base, filter online search results, and combined with the reasoning perspective and headline content, it is forcibly inferred that the headline is not clickbait.\n"
    defense_prompt += "Requirement 1: The headline content is {}.\n"
    defense_prompt += "Requirement 2: Online search content to be filtered: {}.\n"
    defense_prompt += "Requirement 3: Reasoning should start from the following perspectives of the headline, that is, the reasoning perspective is {}.\n"
    defense_prompt += "Requirement 4: Filtering requirements: The filtered results must be highly relevant to the reasoning perspective and headline content, and meet the purpose of determining that the headline is not clickbait.\n"
    defense_prompt += "Requirement 5: Reasoning should be combined with your own knowledge base, headline content, reasoning perspective, and filtered online search content.\n"
    defense_prompt += "Requirement 6: The generated inference content must strongly prove that the headline is not clickbait, and cannot contain uncertain words or expressions such as 'possibility', 'maybe', or 'authenticity'.\n"
    defense_prompt += "Requirement 7: The reasoning must be carried out in the order of reasoning angles, and the reasoning content generated from different reasoning angles is separated by ';'.\n"
    defense_prompt += "Requirement 8: The number of reasoning words should not exceed 120 words.\n"
    defense_prompt += "Requirement 9: Put the output content into [].\n"


    #控方反击
    prosecutor_prompt1 = "Goal: As a prosecutor, my previous statement was not strong enough. This time, I will still use my knowledge base, as well as the headline information and these reasoning angles to **refute** the defense lawyer's statement by filtering real-time search content. This statement must prove the headline is clickbait in a stronger and more convincing way than before. Your stance must consistently assert that the headline is clickbait.\n"
    prosecutor_prompt1 += 'Requirement 1: My previous statement was {}.\n'
    prosecutor_prompt1 += 'Requirement 2: Online search content to be filtered: {}.\n'
    prosecutor_prompt1 += 'Requirement 3: Reasoning should be based on the following perspectives of the headline, that is, the reasoning perspective is {}.\n'
    prosecutor_prompt1 += "Requirement 4: Headline information is {}.\n"
    prosecutor_prompt1 += "Requirement 5: The defense counsel's statement is {}.\n"
    prosecutor_prompt1 += "Requirement 6: The requirement for screening real-time search content is that the filtered results must be highly relevant to this viewpoint and the headline content, and must align with your own position.\n"
    prosecutor_prompt1 += "Requirement 7: The generated reasoning must demonstrate clearly that the headline is clickbait. Do not use uncertain expressions or words like 'authenticity'.\n"
    prosecutor_prompt1 += "Requirement 8: The reasoning must be carried out in the order of reasoning angles, and the reasoning content generated from different reasoning angles is separated by ';'.\n"
    prosecutor_prompt1 += 'Requirement 9: The following are the opinions of the jury members: {}. You may selectively respond to or critique any of their views to strengthen your argument. However, your stance must **not** be changed. If a jury member’s view supports your claim, you may briefly acknowledge it. If it conflicts, respectfully counter it.\n'
    prosecutor_prompt1 += 'Requirement 10: The number of reasoning words should not exceed 120 words.\n'
    prosecutor_prompt1 += 'Requirement 11: Put the output content into [].\n'


    #反驳控方律师
    defense_prompt1 = "Goal: As a defense lawyer, my previous statement was not strong enough. This time, I will still use my knowledge base, combined with headline information and these reasoning angles, to refute the prosecutor's statement by filtering real-time search content. This statement must prove more strongly and convincingly than the previous one that the headline is not clickbait. Your position must be consistent in insisting that the headline is not clickbait.\n"
    defense_prompt1 += "Requirement 1: My previous statement was {}.\n"
    defense_prompt1 += "Requirement 2: Online search content to be filtered: {}.\n"
    defense_prompt1 += "Requirement 3: The reasoning should be based on the following headline perspective, that is, the reasoning perspective is {}.\n"
    defense_prompt1 += "Requirement 4: The headline information is {}.\n"
    defense_prompt1 += "Requirement 5: The prosecutor's statement is {}.\n"
    defense_prompt1 += "Requirement 6: The requirement for filtering real-time search content is that the filtered results must be highly relevant to the viewpoint and headline content, and must be consistent with your own position.\n"
    defense_prompt1 += "Requirement 7: The generated reasoning must clearly show that the headline is not clickbait. Do not use uncertain expressions or words like 'authenticity'.\n"
    defense_prompt1 += "Requirement 8: The reasoning must be carried out in the order of reasoning angles, and the reasoning content generated from different reasoning angles is separated by ';'.\n"
    defense_prompt1 += "Requirement 9: The following are the opinions of the jury members: {}. You may selectively respond to or critique any of their views to strengthen your argument. However, your stance must **not** be changed. If a jury member’s view supports your claim, you may briefly acknowledge it. If it conflicts, respectfully counter it.\n"
    defense_prompt1 += "Requirement 10: The number of reasoning words should not exceed 120 words.\n"
    defense_prompt1 += "Requirement 11: Put the output content into [].\n"



    profession_keywords = {
    "teacher",
    "university_professor",
    "scientist",
    "doctor",
    "psychologist",
    "historian",
    "sociologist",
    "librarian",
    "philosopher",
    "linguist",
    "climate_scientist",
    "lawyer",
    "government_official",
    "political_advisor",
    "civil_servant",
    "police_chief",
    "data_privacy_consultant",
    "entrepreneur",
    "financial_analyst",
    "economist",
    "hr_manager",
    "marketing_specialist",
    "strategy_consultant",
    "venture_capitalist",
    "csr_manager",
    "journalist",
    "media_editor",
    "public_relations_specialist",
    "it_security_officer",
    "independent_media_blogger",
    "fact_checker",
    "software_engineer",
    "cybersecurity_expert",
    "data_scientist",
    "ai_researcher",
    "architectural_engineer",
    "environmental_engineer",
    "community_worker",
    "public_health_officer",
    "sanitation_worker",
    "farmer",
    "bus_driver",
    "local_government_clerk",
    "volunteer_coordinator",
    "artist",
    "writer",
    "religious_leader",
    "activist",
    "museum_curator",
    "average_citizen"

}




    judge_prompt = "Goal: You are the chief judge overseeing the entire debate process. You have access to the full headline content, the prosecution's and defense's evidence sources, all rounds of statements from both sides, and the final comments from all jury members. Your role is to make a final, impartial judgment on whether the headline is clickbait, providing clear reasoning based on all presented information.\n"
    judge_prompt += "Requirement 1: The headline information is {}.\n"
    judge_prompt += "Requirement 2: The prosecution's evidence sources are {}.\n"
    judge_prompt += "Requirement 3: The defense's evidence sources are {}.\n"
    judge_prompt += "Requirement 4: The prosecution's first round of statements was {}.\n"
    judge_prompt += "Requirement 5: The defense's first round of statements was {}.\n"
    judge_prompt += "Requirement 6: The prosecution's second round of statements was {}.\n"
    judge_prompt += "Requirement 7: The defense's second round of statements was {}.\n"
    judge_prompt += "Requirement 8: The final comments from all jury members are: {}.\n"
    judge_prompt += "Requirement 9: As the Chief Judge, please analyze the evidence, arguments, and jury comments to decide whether the headline is clickbait or not. Please provide a detailed explanation of your decision (maximum 100 words), with no line breaks or special characters.\n"
    judge_prompt += "Requirement 10: Make a final binary judgment: output 0 if the headline is not clickbait, 1 if it is clickbait.\n"
    judge_prompt += "Requirement 11: The output format is: what is the reasoning and what is the final_verdict. For example, reasoning: 'The headline that......'; final_verdict: '1'.\n"
    judge_prompt += "Requirement 12: The reasoning content and final_verdict must be separated by a semicolon.\n"




    unshuff_data = pd.read_csv()
 
    data = unshuff_data.sample(frac=1, random_state=42)

    save_path = 
    
    data['view_content'] = None
    data['keywords'] = None
    data['prosecutor_content'] = None
    data['defense_content'] = None 
    data['selected'] = None
    data['first_round_judgements'] = None
    data['prosecutor_content_1'] = None
    data['defense_content_1'] = None
    data['second_round_judgements'] = None
    data['reasoning'] = None
    data['final_verdict'] = None


    for index, row in tqdm(data.iterrows(), total=data.shape[0]):
        print(index, row)
        title = row['title']
        text = row['text']

        if text != None:
          input_text = str(title) + str(text)   
        else : 
          input_text = str(title) 

        """ label = row['label']
        label = int(label)
        #print("新闻标签为",label)
        print("标签为",label) """
        str1 = 'prosecution'
        str2 = 'defense'
        str3 = 'clickbait'
        str4 = 'non-clickbait'



        view_content = "1.Headline Features: Check if the headline uses exaggerated, sensational, or emotional language, and whether it creates unnecessary suspense or curiosity.;2.Headline-Content Consistency: Assess whether the headline accurately reflects the content of the article, or if it is misleading, vague, or overpromising.;3.Specificity and Informativeness: Examine whether the headline provides concrete, specific information (names, numbers, events) or relies on ambiguity and click-attracting phrases.;4.Source and Style Pattern: Analyze if the headline style matches typical clickbait patterns seen in low-credibility websites, and whether similar headlines are used repetitively across platforms.;5.Reader Manipulation: Evaluate whether the headline is designed to provoke emotional reactions, curiosity gaps, or shock value, rather than to inform.;6.Motive and Intent: Determine if the headline appears designed to drive traffic, gain attention, or manipulate reader behavior rather than genuinely inform."
        
        #控方证据来源
        keywords = keyword_prompt.format(str1,str3,input_text,str1,str1,str3)
        keywords = generate_res(keywords)
        search_text_combined_1 = Web_search(keywords)
        
        #辩方证据来源
        keywords = keyword_prompt.format(str2,str4,input_text,str2,str2,str4)
        keywords = generate_res(keywords)
        search_text_combined_2 = Web_search(keywords)

        #控方
        prosecutor_content = prosecutor_prompt.format(input_text, search_text_combined_1, view_content)
        prosecutor_content = generate_res(prosecutor_content)
        #辩方
        defense_content = defense_prompt.format(input_text, search_text_combined_2, view_content)
        defense_content = generate_res(defense_content)


        def select_best_professions_with_prompts(input_text, profession_keywords, get_prompts_func, top_k=7):

            import json
            import ast
            # 获取职业 prompt 字典
            profession_prompts = get_prompts_func()

            # 构造 profession_keywords 字典的字符串表示，用于放入 prompt
            profession_str = json.dumps(list(profession_keywords), ensure_ascii=False)

            # Step 2: 构造 prompt
            prompt = f"""
            Goal: You are a classifier. Based on the category and theme of the headline, please select exactly seven occupations that are the **most relevant** to analyzing whether the headline is clickbait **from the provided jury list ONLY**.

            Requirement 1: The headline content is: {input_text}

            Requirement 2: The available jury members are: {profession_str}

            Requirement 3: You MUST choose only from the occupations listed above. Do NOT include any other occupations — even if they seem relevant. If a word is not listed in the jury list, DO NOT use it.

            Requirement 4: The final output must be exactly 7 occupations, and they must be selected **strictly from the jury list**. Do NOT add general terms like "engineer", "editor", or other professions not in the list. This is a strict classification task. If you output even one word not in the list, the task fails.

            Requirement 5: Output format must be exactly:
            ["occupation_1", "occupation_2", ..., "occupation_7"]
            Each occupation must be in **double quotes**, separated by commas, and inside square brackets. No extra explanation.

            Requirement 6: Example (DO NOT COPY this answer, it is only an example of format):
            If jury = ["linguist", "psychologist", "fact_checker", "influencer", "advertising_specialist", "data_scientist", "teacher"]
            And headline = "You won't believe what this celebrity did last night!"
            Then output = ["linguist", "psychologist", "fact_checker", "advertising_specialist", "influencer", "data_scientist", "teacher"]

            Requirement 7: Use **only occupations that are spelled exactly as listed** in the jury list. No additions, no changes.

            Output:"""

            # 调用 GPT 获取职业选择结果
            gpt_output = generate_res(prompt)

            # 解析模型返回的职业列表
            try:
                selected_professions = ast.literal_eval(gpt_output.strip())
            except Exception as e:
                print("Error parsing GPT output:", e)
                selected_professions = []

            # 映射成 member_1_prompt, ..., member_5_prompt
            prompt_dict = {}
            for i in range(min(len(selected_professions), top_k)):
                prof = selected_professions[i]
                prompt_key = f"member_{i+1}_prompt"
                prompt_dict[prompt_key] = profession_prompts.get(prof, "")

            return selected_professions, prompt_dict

        # 执行筛选与 prompt 映射
        selected, prompt_map = select_best_professions_with_prompts(input_text, profession_keywords, get_profession_prompts)

        member_contents = []
        for i in range(7):
            prompt_key = f"member_{i+1}_prompt"
            prompt_template = prompt_map.get(prompt_key)
            if prompt_template is not None:
                content = generate_res(prompt_template.format(
                    input_text, search_text_combined_1, search_text_combined_2,
                    prosecutor_content, defense_content
                ))
            else:
                print(f"[警告] member_{i+1}（{selected[i] if i < len(selected) else '未知'}）未找到第一轮 Prompt，跳过。")
                content = None
            member_contents.append(content)

        # 汇总第一轮判断结果
        first_round_judgements = ""
        for i in range(7):
            first_round_judgements += f"{selected[i] if i < len(selected) else f'member_{i+1}'}: {member_contents[i]}\n"

        #控方反驳第一轮
        prosecutor_content_1 = prosecutor_prompt1.format(prosecutor_content, search_text_combined_1, view_content, input_text ,defense_content,first_round_judgements)
        prosecutor_content_1 = generate_res(prosecutor_content_1)
        #辩方反驳第一轮
        defense_content_1 = defense_prompt1.format(defense_content, search_text_combined_2, view_content, input_text,prosecutor_content_1,first_round_judgements)
        defense_content_1 = generate_res(defense_content_1)

        def map_second_round_prompts(selected, get_prompts_func):
            prompts_dict = get_prompts_func()
            prompt_map = {}
            for i in range(min(7, len(selected))):
                key = f"member_{i+1}_prompt_2"
                profession = selected[i]
                if profession in prompts_dict:
                    prompt_map[key] = prompts_dict[profession]
                else:
                    print(f"[警告] 未找到职业 '{profession}' 的第二轮 prompt。")
                    prompt_map[key] = None
            return prompt_map
        
        prompt_map_2 = map_second_round_prompts(selected, get_profession2_prompts)
        

        member_contents_2 = []
        for i in range(7):
            prompt_key = f"member_{i+1}_prompt_2"
            prompt_template = prompt_map_2.get(prompt_key)
            if prompt_template is not None:
                content = generate_res(prompt_template.format(
                    input_text, search_text_combined_1, search_text_combined_2,
                    first_round_judgements, prosecutor_content_1, defense_content_1
                ))
            else:
                content = None
            member_contents_2.append(content)

        # 汇总结果
        first_round_judgements_2 = ""
        for i in range(7):
            first_round_judgements_2 += f"{selected[i]}: {member_contents_2[i]}\n"

        #裁判
        judgement_content = judge_prompt.format(input_text,search_text_combined_1,search_text_combined_2,prosecutor_content, defense_content, prosecutor_content_1 ,defense_content_1,first_round_judgements_2)
        judgement_content = generate_res(judgement_content)
        
        reasoning = judgement_content

        # 提取 final_verdict（0 或 1）
        verdict_match = re.search(r"final_verdict:\s*([01])", judgement_content)
        if verdict_match:
            final_verdict = int(verdict_match.group(1))
        else:
            final_verdict = -1
        
        try:

            data.at[index, 'view_content'] = str(view_content)
            data.at[index, 'keywords'] = str(keywords)
            data.at[index, 'prosecutor_content'] = str(prosecutor_content)
            data.at[index, 'defense_content'] = str(defense_content)
            data.at[index, 'selected'] = str(selected) 
            data.at[index, 'first_round_judgements'] = str(first_round_judgements)
            data.at[index, 'prosecutor_content_1'] = str(prosecutor_content_1)
            data.at[index, 'defense_content_1'] = str(defense_content_1)  

            data.at[index, 'second_round_judgements'] = str(first_round_judgements_2)
            data.at[index, 'reasoning'] = str(reasoning)
            data.at[index, 'final_verdict'] = str(final_verdict)
        
        

            # 保存到 CSV 文件
            data.to_csv(save_path, index=False)

        except ValueError as e:
            print(f"Error at index {index}: {e}")


def main():
    run_reason()



if __name__ == '__main__':
    main()
