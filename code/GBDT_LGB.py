#!/usr/bin/python
#  -*- coding: utf-8 -*-
# date: 2018
# author: Kang Yan Zhe
# desc: 千里马 风险识别算法竞赛

import csv
import pandas as pd
import numpy as np
from scipy import interp
import matplotlib.pyplot as plt
from itertools import cycle
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_curve, auc, f1_score
from sklearn.externals import joblib
from lightgbm import LGBMClassifier


def gbdt_feature_selection(fe_name, matrix_x_temp, label_y, th):
    # SelectfromModel
    clf = GradientBoostingClassifier(n_estimators=50, random_state=100)
    clf.fit(matrix_x_temp, label_y)
    sfm = SelectFromModel(clf, prefit=True, threshold=th)
    matrix_x = sfm.transform(matrix_x_temp)

    # 打印出有多少特征重要性非零的特征
    feature_score_dict = {}
    for fn, s in zip(fe_name, clf.feature_importances_):
        feature_score_dict[fn] = s
    m = 0
    for k in feature_score_dict:
        if feature_score_dict[k] == 0.0:
            m += 1
    print 'number of not-zero features:' + str(len(feature_score_dict) - m)

    # 打印出特征重要性
    feature_score_dict_sorted = sorted(feature_score_dict.items(),
                                       key=lambda d: d[1], reverse=True)
    print 'feature_importance:'
    for ii in range(len(feature_score_dict_sorted)):
        print feature_score_dict_sorted[ii][0], feature_score_dict_sorted[ii][1]
    print '\n'

    f = open('../eda/gbdt_feature_importance.txt', 'w')
    f.write('Rank\tFeature Name\tFeature Importance\n')
    for i in range(len(feature_score_dict_sorted)):
        f.write(str(i) + '\t' + str(feature_score_dict_sorted[i][0]) + '\t' + str(feature_score_dict_sorted[i][1]) + '\n')
    f.close()

    # 打印具体使用了哪些字段
    how_long = matrix_x.shape[1]  # matrix_x 是 特征选择后的 输入矩阵
    feature_used_dict_temp = feature_score_dict_sorted[:how_long]
    feature_used_name = []
    for ii in range(len(feature_used_dict_temp)):
        feature_used_name.append(feature_used_dict_temp[ii][0])
    print 'feature_chooesed:'
    for ii in range(len(feature_used_name)):
        print feature_used_name[ii]
    print '\n'

    f = open('../eda/gbdt_feature_chose.txt', 'w')
    f.write('Feature Chose Name :\n')
    for i in range(len(feature_used_name)):
        f.write(str(feature_used_name[i]) + '\n')
    f.close()

    # 找到未被使用的字段名
    feature_not_used_name = []
    for i in range(len(fe_name)):
        if fe_name[i] not in feature_used_name:
            feature_not_used_name.append(fe_name[i])

    # 生成一个染色体（诸如01011100这样的）
    chromosome_temp = ''
    feature_name_ivar = fe_name[:-1]
    for ii in range(len(feature_name_ivar)):
        if feature_name_ivar[ii] in feature_used_name:
            chromosome_temp += '1'
        else:
            chromosome_temp += '0'
    print 'Chromosome:'
    print chromosome_temp
    joblib.dump(chromosome_temp, '../config/chromosome.pkl')
    print '\n'
    return matrix_x, feature_not_used_name, len(feature_used_name)


def data_test_feature_drop(data_test, feature_name_drop):
    # print feature_name_drop
    for col in feature_name_drop:
        data_test.drop(col, axis=1, inplace=True)
    print "data_test_shape:"
    print data_test.shape
    return data_test.as_matrix()


def write_predict_results_to_csv(csv_name, uid, prob_list):

    csv_file = file(csv_name, 'wb')
    writer = csv.writer(csv_file)
    combined_list = [['ID', 'pred']]
    if len(uid) == len(prob_list):
        for i in range(len(uid)):
            combined_list.append([str(uid[i]), str(prob_list[i])])
        writer.writerows(combined_list)
        csv_file.close()
    else:
        print 'no和pred的个数不一致'


def gbdt_lgb_cv_modeling():
    """

    :return:
    """

    '''Data input'''
    data_train = pd.read_csv('../data/train.csv', index_col='ID')
    data_predict = pd.read_csv('../data/pred.csv', index_col='ID')

    '''train 特征工程'''
    data_train_without_label = data_train.drop('Label', axis=1)
    # del data_train_without_label['V17']
    # data_train_without_label['V14×V17'] = data_train_without_label['V14'] * data_train_without_label['V17']
    # data_train_without_label['V14×V4'] = data_train_without_label['V14'] * data_train_without_label['V4']
    # data_train_without_label['V14×V20'] = data_train_without_label['V14'] * data_train_without_label['V20']
    # data_train_without_label['V14×V7'] = data_train_without_label['V14']*data_train_without_label['V7']
    # data_train_without_label['V14×V10'] = data_train_without_label['V14'] * data_train_without_label['V10']
    #
    # data_train_without_label['V17×V4'] = data_train_without_label['V17'] * data_train_without_label['V4']
    # data_train_without_label['V17×V20'] = data_train_without_label['V17'] * data_train_without_label['V20']
    # data_train_without_label['V17×V7'] = data_train_without_label['V17'] * data_train_without_label['V7']
    # data_train_without_label['V17×V10'] = data_train_without_label['V17'] * data_train_without_label['V10']
    #
    # data_train_without_label['V4×V20'] = data_train_without_label['V4'] * data_train_without_label['V20']
    # data_train_without_label['V4×V7'] = data_train_without_label['V4'] * data_train_without_label['V7']
    # data_train_without_label['V4×V10'] = data_train_without_label['V4'] * data_train_without_label['V10']
    #
    # data_train_without_label['V20×V7'] = data_train_without_label['V20'] * data_train_without_label['V7']
    # data_train_without_label['V20×V10'] = data_train_without_label['V20'] * data_train_without_label['V10']
    #
    # data_train_without_label['V7×V10'] = data_train_without_label['V7'] * data_train_without_label['V10']

    feature_name = list(data_train_without_label.columns.values)
    data_predict_user_id = list(data_predict.index.values)

    '''缺失值填充'''
    frames = [data_train_without_label, data_predict]
    data_all = pd.concat(frames)
    data_train_filled = data_train_without_label.fillna(value=data_all.median())

    '''构造训练集和测试集'''
    x_temp = data_train_filled.iloc[:, :].as_matrix()  # 自变量
    y = data_train.iloc[:, -1].as_matrix()  # 因变量

    '''Feature selection'''
    X, dropped_feature_name, len_feature_choose = gbdt_feature_selection(feature_name, x_temp, y, '0.0005*mean')
    # 0.1*mean可以选出10个特征
    # 0.00001*mean可以选出14个特征

    '''处理 验证集 B_test'''
    # del data_predict['V17']

    data_predict_filled = data_predict.fillna(value=data_all.median())
    data_predict_filled_after_feature_selection = data_test_feature_drop(data_predict_filled, dropped_feature_name)

    '''Split train/test data sets'''
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)  # 分层抽样  cv的意思是cross-validation

    '''Choose a classification model'''
    parameter_n_estimators = 100
    classifier = LGBMClassifier(n_estimators=parameter_n_estimators, learning_rate=0.1)

    '''Model fit, predict and ROC'''
    colors = cycle(['cyan', 'indigo', 'seagreen', 'orange', 'blue'])
    lw = 2
    mean_f1 = 0.0
    mean_tpr = 0.0
    mean_fpr = np.linspace(0, 1, 500)
    i_of_roc = 0
    a = 0

    th = 0.3

    for (train_indice, test_indice), color in zip(cv.split(X, y), colors):
        a_model = classifier.fit(X[train_indice], y[train_indice])

        # y_predict_label = a_model.predict(X[test_indice])

        probas_ = a_model.predict_proba(X[test_indice])

        fpr, tpr, thresholds = roc_curve(y[test_indice], probas_[:, 1])

        a += 1  # 序号加1

        mean_tpr += interp(mean_fpr, fpr, tpr)
        mean_tpr[0] = 0.0

        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, lw=lw, color=color, label='ROC fold %d (area = %0.4f)' % (i_of_roc, roc_auc))
        i_of_roc += 1

        label_transformed = probas_[:, 1]
        for i in range(len(label_transformed)):
            if label_transformed[i] > th:
                label_transformed[i] = 1
            else:
                label_transformed[i] = 0
        lt = label_transformed.astype('int32')
        f1 = f1_score(y[test_indice], lt)
        mean_f1 += f1  # 0.7739

    plt.plot([0, 1], [0, 1], linestyle='--', lw=lw, color='k', label='Luck')

    mean_tpr /= cv.get_n_splits(X, y)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    print 'mean_auc=' + str(mean_auc)
    print 'mean_f1=' + str(mean_f1/5)
    plt.plot(mean_fpr, mean_tpr, color='g', linestyle='--', label='Mean ROC (area = %0.4f)' % mean_auc, lw=lw)
    plt.xlim([-0.01, 1.01])
    plt.ylim([-0.01, 1.01])
    plt.xlabel('False Positive Rate mean_f1:'+str(mean_f1))
    plt.ylabel('True Positive Rate')

    plt.title('ROC_gbdt_' + str(len_feature_choose) + '_features_f1_' + str(mean_f1/5))
    plt.legend(loc="lower right")
    plt.savefig('../result/pred_ROC_GL' + '_N_' + str(parameter_n_estimators) + '_features_' + str(len_feature_choose) +
                '_proba_to_label_using_th_' + str(th) + '.png')
    # plt.show()

    a_model = classifier.fit(X, y)

    # label_predict = a_model.predict(data_predict_filled_after_feature_selection)  # 对B_test进行预测
    proba_predict = a_model.predict_proba(data_predict_filled_after_feature_selection)

    '''写入预测出概率的结果'''
    result_file_name = '../result/pred_result_GL_N_' + str(parameter_n_estimators) + '_features_' + str(len_feature_choose) + '_proba.csv'
    write_predict_results_to_csv(result_file_name, data_predict_user_id, proba_predict[:, 1].tolist())

    '''写入要提交的结果'''
    label_transformed = proba_predict[:, 1]
    sum_of_1 = 0
    for i in range(len(label_transformed)):
        if label_transformed[i] > th:
            label_transformed[i] = 1
            sum_of_1 += 1
        else:
            label_transformed[i] = 0
    lt = label_transformed.astype('int32')
    result_file_name = '../result/pred_result_GL_N_' + str(parameter_n_estimators) + '_features_' + str(len_feature_choose) + \
                       '_proba_to_label_using_th_' + str(th) + '_' + str(sum_of_1) + '.csv'
    write_predict_results_to_csv(result_file_name, data_predict_user_id, lt.tolist())

