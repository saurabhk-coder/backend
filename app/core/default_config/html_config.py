
class HtmlMsgConfig:
    INPUT_PASSWORD = """
                    <html><head>
                        </head>

                        <div class="login-page" style="width: 500px;
                        padding: 8% 0 0;
                        margin: auto;">
                            <div class="form" style="position: right;
                        right: 180px;
                        z-index: 1;
                        
                        max-width: 360px;
                        margin: 0 auto 100px;
                        padding: 45px;
                        text-align: center;
                        box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.24);">
                            
                            <h1>Please Enter New Password !!</h1> 
                                <form action={form_url} style="position: relative;
                        z-index: 1;
                        
                        max-width: 360px;
                        margin: 0 auto 100px;
                        padding: 45px;
                        text-align: center;
                        box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.24);" method="post">
                                <input type="hidden" style="font-family: 'Roboto', sans-serif;
                        outline: 0;
                        background: #f2f2f2;
                        width: 100%;
                        border: 0;
                        margin: 0 0 15px;
                        padding: 15px;
                        box-sizing: border-box;
                        font-size: 14px;" id="Password" name="username" value={username}><br><br>
                                <label for="Password">Password:</label><br>
                                <input type="text" style="font-family: 'Roboto', sans-serif;
                        outline: 0;
                        background: #f2f2f2;
                        width: 100%;
                        border: 0;
                        margin: 0 0 15px;
                        padding: 15px;
                        box-sizing: border-box;
                        font-size: 14px;"  id="Password" name="password"><br><br>
                                <label for="Password">Confirm Password:</label><br>
                                <input type="text"  style="font-family: 'Roboto', sans-serif;
                        outline: 0;
                        background: #f2f2f2;
                        width: 100%;
                        border: 0;
                        margin: 0 0 15px;
                        padding: 15px;
                        box-sizing: border-box;
                        font-size: 14px;" id="Password" name="confirm_password"><br><br>
                                <button style="font-family: 'Roboto', sans-serif;
                        text-transform: uppercase;
                        outline: 0;
                        background: #4CAF50;
                        width: 100%;
                        border: 0;
                        padding: 15px;
                        color: #FFFFFF;
                        font-size: 14px;
                        -webkit-transition: all 0.3 ease;
                        transition: all 0.3 ease;
                        cursor: pointer;">Reset</button>
                                </form>
                            </div>
                        </div>
                    </html>"""
    EMAIL_STR = """<html>
                        <head><title>Some HTML in here</title></head>
                        <body style="margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;">
                        <div style="width: 100%; background: #efefef; border-radius: 10px; padding: 10px;">
                        <div style="margin: 0 auto; width: 90%; text-align: center;">
                            <h1 style="background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;">{name}</h1>
                            <div style="margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;">
                            <h3 style="margin-bottom: 100px; font-size: 24px;">{title} !</h3>
                            <h3 style="margin-bottom: 30px;">Verify your e-mail to finish signing up for aaralia;<br>Welcome !</h3>
                            <a style="display: block; margin: 0 auto; border: none; background-color: rgba(255, 214, 10, 1); color: white; width: 200px; line-height: 24px; padding: 10px; font-size: 24px; border-radius: 10px; cursor: pointer; text-decoration: none;"
                                href={url}
                                target="_blank"
                            >
                                Let's Go
                            </a>

                            </div>
                        </div>
                        </div>
                        </body>
                    </html>
                """
    FORGET_EMAIL = """<!DOCTYPE html>
<html>

<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <title>Twinn CRM</title>
</head>
<body style="
      background-color: #f6f6f6;
      font-family: sans-serif;
      -webkit-font-smoothing: antialiased;
      font-size: 14px;
      line-height: 1.4;
      margin: 0;
      padding: 0;
      -ms-text-size-adjust: 100%;
      -webkit-text-size-adjust: 100%;
    ">
  <span class="preheader" style="
        color: transparent;
        display: none;
        height: 0;
        max-height: 0;
        max-width: 0;
        opacity: 0;
        overflow: hidden;
        mso-hide: all;
        visibility: hidden;
        width: 0;
      ">Preview.</span>
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="body" style="
        border-collapse: separate;
        mso-table-lspace: 0pt;
        mso-table-rspace: 0pt;
        background-color: #f6f6f6;
        width: 100%; " width="100%" bgcolor="#f6f6f6">
    <tr>
      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top" valign="top">
        &nbsp;
      </td>
      <td class="container" style="
            font-family: sans-serif;
            font-size: 14px;
            vertical-align: top;
            display: block;
            max-width: 580px;
            padding: 10px;
            width: 580px;
            margin: 0 auto;
          " width="580" valign="top">
        <div class="content" style="
              box-sizing: border-box;
              display: block;
              margin: 0 auto;
              max-width: 580px;
              padding: 10px;
            ">
          <!-- START CENTERED WHITE CONTAINER -->
          <table role="presentation" class="main" style="
                border-collapse: separate;
                mso-table-lspace: 0pt;
                mso-table-rspace: 0pt;
                background: #ffffff;
                border-radius: 3px;
                width: 100%;
              " width="100%">
            <!-- START MAIN CONTENT AREA -->
            <tr>
              <td class="wrapper" style="
                    font-family: sans-serif;
                    font-size: 14px;
                    vertical-align: top;
                    box-sizing: border-box;
                    padding: 20px;
                  " valign="top">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="
                      border-collapse: separate;
                      mso-table-lspace: 0pt;
                      mso-table-rspace: 0pt;
                      width: 100%;
                    " width="100%">
                  <tr>
                    <td style="
                          font-family: sans-serif;
                          font-size: 14px;
                          vertical-align: top;
                        " valign="top">
                      <p style="
                            font-family: sans-serif;
                            font-size: 14px;
                            font-weight: normal;
                            margin: 0;
                            margin-bottom: 15px;
                          ">
                        <svg width="175" height="42" viewBox="0 0 175 42" fill="none"
                          xmlns="http://www.w3.org/2000/svg">
                          <path
                            d="M28.2981 1H3.14715C2.23312 1 1.79815 2.1251 2.47448 2.73994L11.5565 10.9963C11.7405 11.1636 11.9804 11.2564 12.2291 11.2564H37.4468C38.3627 11.2564 38.7967 10.1275 38.1168 9.51397L28.9681 1.25762C28.7844 1.09179 28.5456 1 28.2981 1Z"
                            fill="#FFCE70" stroke="white" stroke-linejoin="round" />
                          <path fill-rule="evenodd" clip-rule="evenodd"
                            d="M40.5611 12.2563C40.5611 11.704 40.1133 11.2563 39.5611 11.2563H12.8433C12.291 11.2563 11.8433 11.704 11.8433 12.2563V39.9997C11.8433 40.552 12.291 40.9997 12.8433 40.9997H18.0217C18.574 40.9997 19.0217 40.552 19.0217 39.9997V20.4616C19.0217 19.9093 19.4694 19.4616 20.0217 19.4616H32.3806C32.9329 19.4616 33.3806 19.9093 33.3806 20.4616V39.9997C33.3806 40.552 33.8283 40.9997 34.3806 40.9997H39.5611C40.1133 40.9997 40.5611 40.552 40.5611 39.9997V12.2563Z"
                            fill="#1CC8EE" />
                          <path
                            d="M10.1732 38.9758L1.40404 31.0418C1.1945 30.8522 1.07495 30.5828 1.07495 30.3002V3.76674C1.07495 2.89973 2.10294 2.44351 2.74586 3.02521L11.515 10.9592C11.7246 11.1488 11.8441 11.4182 11.8441 11.7008V38.2343C11.8441 39.1013 10.8161 39.5575 10.1732 38.9758Z"
                            fill="#80F1D3" stroke="white" stroke-linejoin="round" />
                          <path
                            d="M32.3809 19.4623H20.022C19.4697 19.4623 19.022 19.9101 19.022 20.4623V40.0007C19.022 40.553 19.4697 41.0007 20.022 41.0007H32.3809C32.9332 41.0007 33.3809 40.553 33.3809 40.0007V20.4623C33.3809 19.9101 32.9332 19.4623 32.3809 19.4623Z"
                            fill="#FFCE70" stroke="white" stroke-linejoin="round" />
                          <path
                            d="M38.8901 39.4798L29.6081 31.0416C29.3996 30.8521 29.2808 30.5834 29.2808 30.3017V3.77398C29.2808 2.90584 30.3111 2.45006 30.9534 3.03404L40.2354 11.4722C40.4439 11.6617 40.5628 11.9304 40.5628 12.2122V38.7398C40.5628 39.608 39.5325 40.0638 38.8901 39.4798Z"
                            stroke="white" stroke-linejoin="round" />
                          <rect x="11.8406" y="11.257" width="28.7178" height="29.7434" rx="1" stroke="white"
                            stroke-linejoin="round" />
                          <path d="M11.8406 11.257H40.0455" stroke="white" stroke-linejoin="round" />
                          <path fill-rule="evenodd" clip-rule="evenodd"
                            d="M29.2783 2C29.2783 1.44772 28.8306 1 28.2783 1H1.56055C1.00826 1 0.560547 1.44772 0.560547 2V29.7434C0.560547 30.2957 1.00826 30.7434 1.56055 30.7434H6.73899C7.29128 30.7434 7.73899 30.2957 7.73899 29.7434V10.2053C7.73899 9.65298 8.18671 9.20527 8.73899 9.20527H21.0979C21.6502 9.20527 22.0979 9.65298 22.0979 10.2053V29.7434C22.0979 30.2957 22.5456 30.7434 23.0979 30.7434H28.2783C28.8306 30.7434 29.2783 30.2957 29.2783 29.7434V2Z"
                            fill="#D01865" />
                          <rect x="0.560547" y="1" width="28.7178" height="29.7434" rx="1" stroke="white"
                            stroke-linejoin="round" />
                          <path d="M119.191 41H125.371V18H139.386V41H145.566L145.566 11H119.191V41Z" fill="#221F20" />
                          <path d="M107.825 41H114.005V11H107.825V41Z" fill="#221F20" />
                          <path
                            d="M74.0558 11H80.2358V34H85.3112V23H91.4912V34H96.5679V11H102.748L102.749 41L74.0558 41V11Z"
                            fill="#221F20" />
                          <path d="M62.7991 18H48.5627V11H68.9787L68.9791 41H62.7991V18Z" fill="#221F20" />
                          <path d="M148.105 41H154.285V18H168.3V41H174.48L174.48 11H148.105V41Z" fill="#808184" />
                          <path d="M107.825 7.88889H114.005V1H107.825V7.88889Z" fill="#808184" />
                        </svg>

                      </p>

                      <div style="
                     flex-direction: row;
                     align-items: flex-start;
                     padding: 8px 16px;
                     gap: 8px;
                     
                     width: 506.36px;
                     height: 216px;
                     left: 16px;
                     top: 62px;
                     background: #EFEFEF;
                     border-radius: 8px;">
                        <p style="
                       font-family: sans-serif;
                       font-size: 14px;
                       font-weight: normal;
                       margin: 0;
                       margin-bottom: 15px;
                       color: #565659;
                     ">
                          Hi there
                        </p>

                        <p style="
                        font-family: sans-serif;
                        font-size: 14px;
                        font-weight: normal;
                        margin: 0;
                        margin-bottom: 15px;
                        color: #565659;
                      ">
                        We’ve received a request to reset your password. Please use this code to reset the password
                        for the TWINN account.click on link {url}</p>

                        <p style="
                        font-family: sans-serif;
                        font-size: 14px;
                        font-weight: normal;
                        margin-top:24px;
                        margin-bottom: 24px;
                        color: #565659;">
                      Here is your code: 
                      <span style="font-size: 16px;
                      font-weight: 600;
                      color: #000000;">
                      {otp}
                    </span> 
                      </p>
                      <p style="
                      font-family: sans-serif;
                      font-size: 14px;
                      font-weight: normal;
                      margin: 0;
                      margin-bottom: 0px;
                      color: #565659;
                    ">
                     If you didn’t make the request, just ignore this message .
                    </p>
                   
                  <p style="
                  font-family: sans-serif;
                  font-size: 14px;
                  font-weight: normal;
                  margin: 0;
                  color: #565659;
                ">
                Thanks
                </p>
                <p style="
                font-family: sans-serif;
                font-size: 14px;
                font-weight: normal;
                margin: 0;
                color: #565659;
              ">
             TWINN Team
              </p>
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td>

                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- END MAIN CONTENT AREA -->
          </table>
          <!-- END CENTERED WHITE CONTAINER -->

          <!-- START FOOTER -->
          <div class="footer" style="
                clear: both;
                margin-top: 10px;
                text-align: center;
                width: 100%;
              ">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="
                  border-collapse: separate;
                  mso-table-lspace: 0pt;
                  mso-table-rspace: 0pt;
                  width: 100%;
                " width="100%">
              <tr>
                <td class="content-block" style="
                      font-family: sans-serif;
                      vertical-align: top;
                      padding-bottom: 10px;
                      padding-top: 10px;
                      color: #999999;
                      font-size: 12px;
                      text-align: center;
                    " valign="top" align="center">
                  <span class="apple-link" style="
                        color: #999999;
                        font-size: 12px;
                        text-align: center;
                      ">Twinn Team</span>
                  <br />
                  <!-- Don't like these emails?
                  <a href="#" style="
                        text-decoration: underline;
                        color: #999999;
                        font-size: 12px;
                        text-align: center;
                      ">Unsubscribe</a>. -->
                </td>
              </tr>
              <tr>
                <!-- <td class="content-block powered-by" style="font-family: sans-serif; vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #999999; font-size: 12px; text-align: center;" valign="top" align="center">
                    Powered by <a href="#" style="color: #999999; font-size: 12px; text-align: center; text-decoration: none;">HTMLemail</a>.
                  </td> -->
              </tr>
            </table>
          </div>
          <!-- END FOOTER -->
        </div>
      </td>
      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top" valign="top">
        &nbsp;
      </td>
    </tr>
  </table>
</body>

</html>
                """
    NONE_MSG = """<html><head>
								<title>Some HTML in here</title>
							</head>
							<body>
								<style type="text/css">
                                body {
                                    text-align: center;
                                    padding: 40px 0;
                                    background: #EBF0F5;
                                }
                                h1 {
                                    color: #88B04B;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-weight: 900;
                                    font-size: 40px;
                                    margin-bottom: 10px;
                                    }
                                    p {
                                    color: #404F5E;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-size: 16px;
                                    margin: 0;
                                    }
                                i {
                                    color: #9ABC66;
                                    font-size: 100px;
                                    line-height: 200px;
                                    margin-left:-15px;
                                }
                                .success_art {
                                    background: white;
                                    padding: 60px;
                                    border-radius: 4px;
                                    box-shadow: 0 2px 3px #C8D0D8;
                                    display: inline-block;
                                    margin: 0 auto;
                                }
                                </style>
                            </style>
                            <div class="container">
                            <div class="success_art">
                                <div style="border-radius:200px; height:200px; width:200px; background: #F8FAF5; margin:0 auto;">
                                <i class="checkmark">✓</i>
                                </div>
                                <h1>Error</h1> 
                                <p>User Does't Exists;<br/> Please,Check your mail!</p>
                            </div>
                            </div>
                                </body>
                            </html>
						"""
    ACTIVE_MSG = """<html><head>
								<title>Some HTML in here</title>
							</head>
							<body>
								<style type="text/css">
                                body {
                                    text-align: center;
                                    padding: 40px 0;
                                    background: #EBF0F5;
                                }
                                h1 {
                                    color: #88B04B;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-weight: 900;
                                    font-size: 40px;
                                    margin-bottom: 10px;
                                    }
                                    p {
                                    color: #404F5E;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-size: 16px;
                                    margin: 0;
                                    }
                                i {
                                    color: #9ABC66;
                                    font-size: 100px;
                                    line-height: 200px;
                                    margin-left:-15px;
                                }
                                .success_art {
                                    background: white;
                                    padding: 60px;
                                    border-radius: 4px;
                                    box-shadow: 0 2px 3px #C8D0D8;
                                    display: inline-block;
                                    margin: 0 auto;
                                }
                                </style>
                            </style>
                            <div class="container">
                            <div class="success_art">
                                <div style="border-radius:200px; height:200px; width:200px; background: #F8FAF5; margin:0 auto;">
                                <i class="checkmark">✕</i>
                                </div>
                                <h1>Error</h1> 
                                <p>User Already Exists !</p>
                            </div>
                            </div>
                                </body>
                            </html>
						"""
    
    DATE_EXPIRED ="""<html><head>
								<title>Some HTML in here</title>
							</head>
							<body>
								<style type="text/css">
                                body {
                                    text-align: center;
                                    padding: 40px 0;
                                    background: #EBF0F5;
                                }
                                h1 {
                                    color: #88B04B;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-weight: 900;
                                    font-size: 40px;
                                    margin-bottom: 10px;
                                    }
                                    p {
                                    color: #404F5E;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-size: 16px;
                                    margin: 0;
                                    }
                                i {
                                    color: #9ABC66;
                                    font-size: 100px;
                                    line-height: 200px;
                                    margin-left:-15px;
                                }
                                .success_art {
                                    background: white;
                                    padding: 60px;
                                    border-radius: 4px;
                                    box-shadow: 0 2px 3px #C8D0D8;
                                    display: inline-block;
                                    margin: 0 auto;
                                }
                                </style>
                            </style>
                            <div class="container">
                            <div class="success_art">
                                <div style="border-radius:200px; height:200px; width:200px; background: #F8FAF5; margin:0 auto;">
                                <i class="checkmark">✕</i>
                                </div>
                                <h1>Error</h1> 
                                <p>Oops! Session Expired;</p>
                            </div>
                            </div>
                                </body>
                            </html>
						"""
    SUCCESS_MSG="""<html><head>
								<title>Some HTML in here</title>
							</head>
							<body>
								<style type="text/css">
                                body {
                                    text-align: center;
                                    padding: 40px 0;
                                    background: #EBF0F5;
                                }
                                h1 {
                                    color: #88B04B;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-weight: 900;
                                    font-size: 40px;
                                    margin-bottom: 10px;
                                    }
                                    p {
                                    color: #404F5E;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-size: 16px;
                                    margin: 0;
                                    }
                                i {
                                    color: #9ABC66;
                                    font-size: 100px;
                                    line-height: 200px;
                                    margin-left:-15px;
                                }
                                .success_art {
                                    background: white;
                                    padding: 60px;
                                    border-radius: 4px;
                                    box-shadow: 0 2px 3px #C8D0D8;
                                    display: inline-block;
                                    margin: 0 auto;
                                }
                                </style>
                            </style>
                            <div class="container">
                            <div class="success_art">
                                <div style="border-radius:200px; height:200px; width:200px; background: #F8FAF5; margin:0 auto;">
                                <i class="checkmark">✓</i>
                                </div>
                                <h1>Success</h1> 
                                <p>Email Verified Successfully;</p>
                            </div>
                            </div>
                                </body>
                            </html>
						"""
    PASSWORD_UPDATE="""<html><head>
								<title>Some HTML in here</title>
							</head>
							<body>
								<style type="text/css">
                                body {
                                    text-align: center;
                                    padding: 40px 0;
                                    background: #EBF0F5;
                                }
                                h1 {
                                    color: #88B04B;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-weight: 900;
                                    font-size: 40px;
                                    margin-bottom: 10px;
                                    }
                                    p {
                                    color: #404F5E;
                                    font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
                                    font-size: 16px;
                                    margin: 0;
                                    }
                                i {
                                    color: #9ABC66;
                                    font-size: 100px;
                                    line-height: 200px;
                                    margin-left:-15px;
                                }
                                .success_art {
                                    background: white;
                                    padding: 60px;
                                    border-radius: 4px;
                                    box-shadow: 0 2px 3px #C8D0D8;
                                    display: inline-block;
                                    margin: 0 auto;
                                }
                                </style>

                            </style>
                            <div class="container">
                            <div class="success_art">
                                <div style="border-radius:200px; height:200px; width:200px; background: #F8FAF5; margin:0 auto;">
                                <i class="checkmark">✓</i>
                                </div>
                                <h1>Success</h1> 
                                <p>Password Updated Successfully;</p>
                            </div>
                            </div>
                                </body>
                            </html>
						"""
