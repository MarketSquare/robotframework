*** Settings ***
Suite Setup       Run Tests    ${EMPTY}    running/if/invalid_if.robot
Test Template     Branch statuses should be
Resource          atest_resource.robot

*** Test Cases ***
IF without condition
    FAIL

IF without condition with ELSE
    FAIL    NOT RUN

IF with invalid condition
    FAIL

IF with invalid condition with ELSE
    FAIL    NOT RUN

IF condition with non-existing variable
    FAIL    NOT RUN

ELSE IF with invalid condition
    NOT RUN    NOT RUN    FAIL    NOT RUN    NOT RUN

IF without END
    FAIL

Invalid END
    FAIL

IF with wrong case
    [Template]    NONE
    Check Test Case    ${TEST NAME}

ELSE IF without condition
    FAIL    NOT RUN    NOT RUN

ELSE IF with multiple conditions
    [Template]    NONE
    ${tc} =    Branch statuses should be    FAIL    NOT RUN    NOT RUN
    Should Be Equal    ${tc.body[0].body[1].condition}    \${False}, ooops, \${True}

ELSE with condition
    FAIL    NOT RUN

IF with empty body
    FAIL

ELSE with empty body
    FAIL    NOT RUN

ELSE IF with empty body
    FAIL    NOT RUN    NOT RUN

ELSE after ELSE
    FAIL    NOT RUN    NOT RUN

ELSE IF after ELSE
    FAIL    NOT RUN    NOT RUN

Invalid IF inside FOR
    FAIL

Multiple errors
    FAIL    NOT RUN    NOT RUN    NOT RUN    NOT RUN

*** Keywords ***
Branch statuses should be
    [Arguments]    @{statuses}
    ${tc} =    Check Test Case    ${TESTNAME}
    Should Be Equal    ${tc.body[0].status}    FAIL
    FOR    ${branch}    ${status}    IN ZIP    ${tc.body[0].body}    ${statuses}
        Should Be Equal    ${branch.status}    ${status}
    END
    Should Be Equal    ${{len($tc.body[0].body)}}    ${{len($statuses)}}
    RETURN    ${tc}
