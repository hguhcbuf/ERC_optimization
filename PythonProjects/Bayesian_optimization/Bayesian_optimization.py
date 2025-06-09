import os
import pandas as pd
from bayes_opt import BayesianOptimization
from bayes_opt import acquisition

def eyeball_bayesian(excel_path, var1, var2, var1_min, var1_max, var2_min, var2_max, max_iter):
    
    columns = ["iter", str(var1), str(var2), "score"]
    acq = acquisition.ExpectedImprovement(xi=0.2)

    optimizer = BayesianOptimization(
        f=None,
        acquisition_function=acq,
        pbounds={columns[1]: (var1_min, var1_max), columns[2]: (var2_min, var2_max)},
        verbose=2,
        random_state=1,
    )

    if not os.path.exists(excel_path):
        df = pd.DataFrame(columns=columns)
        df.to_excel(excel_path, index=False)
        print(f"엑셀파일 만듦 : {excel_path}")
    else:
        try:
            df = pd.read_excel(excel_path)
            existing = df.columns.tolist()
            if existing != columns:
                df = pd.DataFrame(columns=columns)
                df.to_excel(excel_path, index=False)
                print("변수 이름 바꿨네?")
            
            params_list = df[[columns[1], columns[2]]].to_dict(orient="records")
            targets = df["score"].astype(float).tolist()
            for params, target in zip(params_list, targets):
                optimizer.register(params=params, target=target)
            print(f'{len(targets)}개 실험값 등록 완료')
        except:
            print('문제발생 : 카톡해')
            
    print('-'*80)
    count = int(df["iter"].max())+1 if not df.empty else 1
    for _ in range(max_iter):
        try:
            print(f'실험 #{count}')
            next_param = optimizer.suggest()
            rounded_param = {k: round(v) for k, v in next_param.items()}
            print(f'이 값으로 실험을 해라 혜연아 : {rounded_param}')
            target = float(input('얼른 실험해라 뭐하냐 : '))
            optimizer.register(params=next_param, target=target)
        except ValueError:
            count = int(df["iter"].max())+1 if not df.empty else 1
            print('숫자를 넣어라 혜연아..')
            break
        new_row = {'iter':count, 'speed':next_param['speed'], 'angle':next_param['angle'], 'score':target}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(excel_path, index=False)
        count+=1
        print('-'*80)
    return