def replacevar(s): # this replace all %%var%% in string s by var value
    n1=s.find('%%')
    while n1>-1:
        n1+=2
        n2 = n1 + s[n1:].find('%%')
        try:
            v = eval(s[n1:n2])
        except:
            v = ''
            pass
        s = s[:n1-2]+v+s[n2+2:]
        n1=s.find('%%')
    return s
